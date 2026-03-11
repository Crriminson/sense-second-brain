# orchestration/pipeline.py
"""
The central pipeline. All input flows through process_text().
Connects AI, Database, Vector, and WebSocket layers.
"""

from asyncio import create_task
from database import crud
from vector import store as vector
from ai import brain as ai
from ws_manager import manager
from mqtt_handler import publish_feedback


# ═══════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════

async def process_text(text: str) -> dict:
    """
    Text in → classify → execute → respond.

    Called by:
    - Phone WebSocket (after Android STT)
    - REST POST /api/process (typed input)
    - MQTT button handler (triggers recording flow)
    """

    active_ws = await crud.get_active_workspace()
    ws_name = active_ws["name"] if active_ws else "General"

    # Step 1: What does the user want?
    classified = await ai.classify_intent(text, ws_name)
    intent = classified["intent"]

    # Step 2: Do it
    if intent == "create_note":
        return await _handle_create_note(text, classified)

    elif intent == "query_notes":
        return await _handle_query(text, classified)

    elif intent == "switch_workspace":
        return await _handle_switch(classified)

    elif intent == "start_meeting":
        return await _handle_start_meeting()

    elif intent == "end_meeting":
        return await _handle_end_meeting()

    elif intent == "list_workspaces":
        return await _handle_list_workspaces()

    elif intent == "list_notes":
        return await _handle_list_notes(active_ws)

    # Fallback
    return {
        "intent": "unknown",
        "spoken_response": classified.get(
            "spoken_response", "I'm not sure what to do with that."
        ),
    }


# ═══════════════════════════════════════
#  INTENT HANDLERS
# ═══════════════════════════════════════

async def _handle_create_note(text: str, classified: dict) -> dict:
    # Resolve workspace if user mentioned one
    workspace_id = None
    if classified["workspace"]:
        ws = await crud.switch_workspace(classified["workspace"])
        workspace_id = ws["id"]
        await manager.broadcast_ui("workspace_switched", ws)

    # Save to SQLite
    note = await crud.save_note(
        raw_text=classified["text"] or text,
        tags=classified["tags"],
        summary=(classified["text"] or text)[:80],
        workspace_id=workspace_id,
    )

    # Save to ChromaDB
    vector.add_note(
        note["id"], note["raw_text"],
        note["workspace_name"], note["tags"]
    )

    # Push to UI
    await manager.broadcast_ui("note_created", note)

    # Background: compute edges (user doesn't wait)
    create_task(_compute_edges(note))

    # ESP32 feedback
    create_task(publish_feedback("buzz_1"))

    return {
        "intent": "create_note",
        "note": note,
        "spoken_response": classified["spoken_response"],
    }


async def _handle_query(text: str, classified: dict) -> dict:
    question = classified["query"] or text

    # Vector search
    relevant = vector.search(question, top_k=5)

    # Enrich with edge context (contradictions matter for answers)
    enriched = relevant.copy()
    for note in relevant[:3]:
        edges = await crud.get_edges(note["id"])
        for edge in edges:
            if edge["rel_type"] == "contradicts":
                enriched.append({
                    "text": (
                        f"⚠️ CONFLICT: '{edge['source_text'][:80]}' "
                        f"was contradicted by '{edge['target_text'][:80]}'"
                    ),
                    "workspace": "",
                })

    # LLM synthesizes answer
    answer = await ai.answer_question(question, enriched)

    return {
        "intent": "query_notes",
        "answer": answer,
        "sources": relevant,
        "spoken_response": answer,
    }


async def _handle_switch(classified: dict) -> dict:
    target = classified["workspace"]
    if not target:
        return {
            "intent": "switch_workspace",
            "spoken_response": "Which workspace do you want to switch to?",
        }

    ws = await crud.switch_workspace(target)
    await manager.broadcast_ui("workspace_switched", ws)
    create_task(publish_feedback("buzz_2"))

    return {
        "intent": "switch_workspace",
        "workspace": ws,
        "spoken_response": classified["spoken_response"],
    }


async def _handle_start_meeting() -> dict:
    try:
        session = await crud.start_session()
        await manager.broadcast_ui("session_started", session)
        await manager.send_to_phone("start_capture", {
            "mode": "meeting",
            "session_id": session["id"],
        })
        return {
            "intent": "start_meeting",
            "session": session,
            "spoken_response": "Meeting mode started. I'm recording.",
        }
    except ValueError as e:
        return {
            "intent": "start_meeting",
            "spoken_response": str(e),
        }


async def _handle_end_meeting() -> dict:
    active = await crud.get_active_session()
    if not active:
        return {
            "intent": "end_meeting",
            "spoken_response": "No active meeting to end.",
        }

    return await end_meeting_session(active["id"])


async def _handle_list_workspaces() -> dict:
    workspaces = await crud.list_workspaces()
    names = ", ".join(w["name"] for w in workspaces)
    return {
        "intent": "list_workspaces",
        "workspaces": workspaces,
        "spoken_response": f"Your workspaces: {names}" if names else "No workspaces yet.",
    }


async def _handle_list_notes(active_ws: dict | None) -> dict:
    ws_id = active_ws["id"] if active_ws else None
    ws_name = active_ws["name"] if active_ws else "General"
    notes = await crud.list_notes(workspace_id=ws_id, limit=10)
    return {
        "intent": "list_notes",
        "notes": notes,
        "spoken_response": f"You have {len(notes)} notes in {ws_name}.",
    }


# ═══════════════════════════════════════
#  MEETING END (used by pipeline + MQTT)
# ═══════════════════════════════════════

async def end_meeting_session(session_id: str) -> dict:
    """End meeting, summarize, save summary as note."""
    session = await crud.get_session(session_id)

    if not session or not session.get("transcript", "").strip():
        await crud.end_session(session_id)
        return {
            "intent": "end_meeting",
            "spoken_response": "Meeting ended. No transcript to summarize.",
        }

    # Summarize
    summary_data = await ai.summarize_transcript(session["transcript"])

    # Update session
    result = await crud.end_session(
        session_id,
        summary=summary_data.get("summary"),
        action_items=summary_data.get("action_items", []),
    )

    # Save summary as a note
    note_text = f"Meeting Summary:\n{summary_data['summary']}"
    items = summary_data.get("action_items", [])
    if items:
        note_text += "\n\nAction Items:\n" + "\n".join(
            f"- {item}" for item in items
        )

    note = await crud.save_note(
        raw_text=note_text,
        tags=["meeting", "summary"],
        summary=summary_data["summary"],
    )
    vector.add_note(
        note["id"], note["raw_text"],
        note["workspace_name"], note["tags"]
    )

    await manager.broadcast_ui("note_created", note)
    await manager.broadcast_ui("session_ended", result)
    create_task(publish_feedback("buzz_2"))

    action_count = len(items)
    return {
        "intent": "end_meeting",
        "session": result,
        "summary": summary_data,
        "spoken_response": (
            f"Meeting saved. {summary_data['summary']} "
            f"{action_count} action items found."
        ),
    }


# ═══════════════════════════════════════
#  BACKGROUND EDGE COMPUTATION
# ═══════════════════════════════════════

async def _compute_edges(note: dict):
    """
    Runs AFTER response is sent to user.
    Finds similar notes, classifies relationships, stores edges.
    Pushes graph update to UI when done.
    """
    try:
        similar = vector.search(note["raw_text"], top_k=3)
        new_edges = []

        for sim in similar:
            # Skip self and weak matches
            if sim["id"] == note["id"] or sim["similarity"] < 0.5:
                continue

            # Ask LLM how these relate
            rel = await ai.classify_relationship(
                note["raw_text"], sim["text"]
            )

            if rel["rel_type"] != "none":
                edge = await crud.save_edge(
                    source_id=note["id"],
                    target_id=sim["id"],
                    rel_type=rel["rel_type"],
                    weight=rel["weight"],
                    explanation=rel["explanation"],
                )
                if edge:
                    new_edges.append(edge)

        # Push graph update to UI
        if new_edges:
            graph = await crud.get_graph()
            await manager.broadcast_ui("graph_update", graph)

            # Alert on contradictions
            contradictions = [
                e for e in new_edges if e["rel_type"] == "contradicts"
            ]
            if contradictions:
                await manager.broadcast_ui("proactive_alert", {
                    "message": (
                        f"Possible contradiction: "
                        f"{contradictions[0]['explanation']}"
                    ),
                    "edge": contradictions[0],
                })
                await manager.send_to_phone("alert", {
                    "message": contradictions[0]["explanation"],
                })

    except Exception as e:
        print(f"[EDGES] Background computation failed: {e}")
