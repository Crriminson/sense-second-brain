"""
Main orchestration pipeline.
The conductor — routes everything, coordinates all layers.

Changes from previous version:
  - 3 new handlers: delete_note, general_query, greeting
  - Enhanced context: workspace summaries + tag cloud
  - Fuzzy workspace matching with difflib SequenceMatcher
  - Error buffer: failed inputs stored, reprocessed on demand
"""

from datetime import datetime
from difflib import SequenceMatcher

from ai import intents, answers, provider
from store.sql import notes as sql_notes, workspaces as sql_workspaces, sessions as sql_sessions
from store.sql import user_profile
from store import vectors as vector_store
from system import commands as sys_commands
from engine import memory
from engine.tasks import compute_edges
from config import settings


# ═══════════════════════════════════════════════════
#  ERROR BUFFER — stores failed inputs for retry
# ═══════════════════════════════════════════════════

_error_buffer: list[dict] = []
_MAX_BUFFER_SIZE = 10


# ═══════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════

async def process_text(text: str) -> dict:
    """
    Main entry point. Text in → structured result out.
    Called by the WebSocket handler when phone sends speech.
    """
    text = text.strip()
    if not text:
        return {"intent": "none", "spoken_response": "I didn't catch that.", "data": {}}

    print(f"\n{'='*50}")
    print(f"[ENGINE] Input: '{text}'")

    # 1. Build context for the AI
    context = await _build_context()

    # 2. Classify intent
    classified = await intents.classify(text, context=context)
    intent = classified["intent"]
    print(f"[ENGINE] Intent: {intent} ({classified['confidence']})")

    # 3. Route to the right handler
    result_data = {}
    try:
        handler = INTENT_HANDLERS.get(intent)
        if handler:
            result_data = await handler(classified, text, context)
        else:
            print(f"[ENGINE] No handler for intent: {intent}")
    except Exception as e:
        print(f"[ENGINE] Handler error: {e}")
        classified["spoken_response"] = "Something went wrong, but I saved your input."
        try:
            ws_id = context.get("active_workspace_id")
            note = await sql_notes.save(
                raw_text=text, tags=["needs-review"],
                workspace_id=ws_id, source="voice",
            )
            _add_to_buffer(text, context, note["id"])
        except Exception as buf_err:
            print(f"[ENGINE] Buffer save also failed: {buf_err}")

    # 4. Update conversation memory
    memory.add_turn(text, classified["spoken_response"], intent)

    # 5. Learn from this interaction
    try:
        ws_name = context.get("active_workspace", "General")
        tags = classified.get("tags", [])
        await user_profile.update_from_interaction(tags, ws_name)
    except Exception as e:
        print(f"[ENGINE] Profile update failed (non-critical): {e}")

    # 6. Return
    classified["data"] = result_data
    print(f"[ENGINE] Response: '{classified['spoken_response']}'")
    print(f"{'='*50}\n")
    return classified


# ═══════════════════════════════════════════════════
#  CONTEXT BUILDER
# ═══════════════════════════════════════════════════

async def _build_context() -> dict:
    """Gather all dynamic context for intent classification."""

    # Active workspace
    active_ws = await sql_workspaces.get_active()
    ws_name = active_ws["name"] if active_ws else "General"
    ws_id = active_ws["id"] if active_ws else None

    # All workspaces + summaries with note counts
    all_ws = await sql_workspaces.list_all()
    ws_summary_parts = []
    for w in all_ws[:10]:
        try:
            nc = await sql_notes.count(workspace_id=w["id"])
            marker = " (active)" if w.get("is_active") else ""
            ws_summary_parts.append(f"{w['name']}{marker}, {nc} notes")
        except Exception:
            ws_summary_parts.append(w["name"])
    ws_summaries = " | ".join(ws_summary_parts) if ws_summary_parts else "General (active, 0 notes)"

    # Recent notes — fetch 20 for tag stats, display top 5
    all_recent = []
    if ws_id:
        all_recent = await sql_notes.list_all(workspace_id=ws_id, limit=20)

    recent_text = "\n".join(
        f"- {n['raw_text'][:60]}" for n in all_recent[:5]
    ) if all_recent else ""

    # Tag cloud — frequency-sorted from recent notes
    tag_freq: dict[str, int] = {}
    for n in all_recent:
        for t in n.get("tags", []):
            if t and isinstance(t, str):
                tag_freq[t] = tag_freq.get(t, 0) + 1
    tag_cloud = ", ".join(
        t for t, _ in sorted(tag_freq.items(), key=lambda x: -x[1])[:10]
    )

    # Conversation history
    conv = memory.get_recent(5)

    # User profile
    try:
        profile = await user_profile.get_profile_string()
    except Exception:
        profile = ""

    return {
        # Used by intents.build_prompt
        "active_workspace": ws_name,
        "workspace_summaries": ws_summaries,
        "tag_cloud": tag_cloud,
        "recent_notes": recent_text,
        "conversation_history": conv,
        "user_profile": profile,
        # Used by handlers
        "active_workspace_id": ws_id,
        "all_workspaces": all_ws,
    }


# ═══════════════════════════════════════════════════
#  INTENT HANDLERS
# ═══════════════════════════════════════════════════

async def _handle_create_note(classified: dict, original_text: str, context: dict) -> dict:
    ws_id = context.get("active_workspace_id")
    ws_name = context.get("active_workspace", "General")

    note_text = classified.get("text") or original_text
    tags = classified.get("tags", [])

    # If user mentioned a specific workspace, switch first
    target_ws = classified.get("workspace")
    if target_ws:
        matched = _fuzzy_match_workspace(target_ws, context.get("all_workspaces", []))
        ws = await sql_workspaces.switch(matched or target_ws)
        ws_id = ws["id"]
        ws_name = ws["name"]

    note = await sql_notes.save(
        raw_text=note_text,
        tags=tags,
        workspace_id=ws_id,
        source="voice",
    )

    vector_store.add(
        note_id=note["id"],
        text=note["raw_text"],
        workspace=ws_name,
        tags=tags,
    )

    compute_edges.delay(note["raw_text"], note["id"])

    note_count = await sql_notes.count(workspace_id=ws_id)
    if classified.get("spoken_response") in ("Got it, noted.", "I saved that as a note.", ""):
        classified["spoken_response"] = f"Saved to {ws_name}. That's note #{note_count}."

    return {"note": note}


async def _handle_update_note(classified: dict, original_text: str, context: dict) -> dict:
    """
    Update/append to an existing note.

    Uses classified["query"] to find which note to update.
    Uses classified["text"] for the new content to add.

    Strategy:
      1. Check conversation memory — if last action was create_note, update that one
      2. Otherwise, vector search to find the best matching note
      3. Append new content to the matched note
      4. Re-embed in vector store
    """
    ws_id = context.get("active_workspace_id")
    ws_name = context.get("active_workspace", "General")

    new_content = classified.get("text") or original_text
    search_query = classified.get("query") or original_text

    target_note = None

    # Strategy 1: If last action was create_note, user probably means "add to THAT"
    last_turn = memory.get_last_turn()
    if last_turn and last_turn["intent"] == "create_note":
        # Get the most recent note in this workspace
        recent = await sql_notes.list_all(workspace_id=ws_id, limit=1)
        if recent:
            target_note = recent[0]

    # Strategy 2: Vector search to find the matching note
    if not target_note:
        results = vector_store.search(search_query, top_k=3, workspace=ws_name)

        # Fall back to global search
        if not results:
            results = vector_store.search(search_query, top_k=3)

        if results:
            # Get the full note from SQLite (vector store only has text)
            best_match = results[0]
            target_note = await sql_notes.get(best_match["id"])

    # No note found — create a new one instead
    if not target_note:
        classified["spoken_response"] = f"Couldn't find that note, so I saved it as a new one."

        note = await sql_notes.save(
            raw_text=new_content,
            tags=classified.get("tags", []),
            workspace_id=ws_id,
            source="voice",
        )

        vector_store.add(
            note_id=note["id"],
            text=note["raw_text"],
            workspace=ws_name,
            tags=classified.get("tags", []),
        )

        return {"note": note, "action": "created_new"}

    # Found the note — append new content
    old_text = target_note["raw_text"]
    updated_text = f"{old_text}\n{new_content}"

    # Merge tags — old tags + new tags, deduped
    old_tags = target_note.get("tags", [])
    if isinstance(old_tags, str):
        import json
        try:
            old_tags = json.loads(old_tags)
        except Exception:
            old_tags = []

    new_tags = classified.get("tags", [])
    merged_tags = list(dict.fromkeys(old_tags + new_tags))  # dedup preserving order

    # Update in SQLite
    updated_note = await sql_notes.update(
        note_id=target_note["id"],
        raw_text=updated_text,
        tags=merged_tags,
    )

    # Re-embed in vector store with the full updated text
    vector_store.delete(target_note["id"])
    vector_store.add(
        note_id=target_note["id"],
        text=updated_text,
        workspace=ws_name,
        tags=merged_tags,
    )

    preview = old_text[:40]
    classified["spoken_response"] = f"Updated the note: '{preview}'. Added your new info."

    return {"note": updated_note, "action": "updated", "original_text": old_text}


async def _handle_query_notes(classified: dict, original_text: str, context: dict) -> dict:
    query = classified.get("query") or original_text
    ws_name = context.get("active_workspace")

    # Search current workspace first
    results = vector_store.search(query, top_k=5, workspace=ws_name)

    # Fall back to global search
    if not results:
        results = vector_store.search(query, top_k=5)

    # Gather edge context for richer answers
    edge_context = []
    try:
        from store.sql import edges as sql_edges
        if results:
            for r in results[:2]:
                edges = await sql_edges.get_for_note(r["id"])
                for e in edges:
                    edge_context.append({
                        "rel_type": e["rel_type"],
                        "source_text": e.get("source_text", ""),
                        "target_text": e.get("target_text", ""),
                    })
    except Exception:
        pass

    answer_text = await answers.answer(query, results, edge_context)
    classified["spoken_response"] = answer_text

    return {"query": query, "results_count": len(results)}


async def _handle_delete_note(classified: dict, original_text: str, context: dict) -> dict:
    """
    Delete notes. Handles:
      - "delete that" / "scratch that"         -> deletes most recent 1
      - "delete all notes" / "clear workspace" -> deletes all in workspace
    """
    ws_id = context.get("active_workspace_id")
    ws_name = context.get("active_workspace", "General")

    # Check if user wants to delete ALL
    text_lower = original_text.lower()
    delete_all = any(word in text_lower for word in ["all", "everything", "clear", "wipe"])

    if delete_all:
        notes = await sql_notes.list_all(workspace_id=ws_id, limit=500)

        if not notes:
            classified["spoken_response"] = f"No notes to delete in {ws_name}."
            return {}

        count = 0
        for note in notes:
            try:
                await sql_notes.delete(note["id"])
                vector_store.delete(note["id"])
                count += 1
            except Exception:
                continue

        classified["spoken_response"] = f"Deleted all {count} notes from {ws_name}."
        return {"deleted_count": count}

    # Delete most recent note only
    recent = await sql_notes.list_all(workspace_id=ws_id, limit=1)

    if not recent:
        classified["spoken_response"] = f"No notes to delete in {ws_name}."
        return {}

    note = recent[0]
    preview = note["raw_text"][:50]

    await sql_notes.delete(note["id"])
    vector_store.delete(note["id"])

    classified["spoken_response"] = f"Deleted: '{preview}'."
    return {"deleted_note": note}


async def _handle_general_query(classified: dict, original_text: str, context: dict) -> dict:
    """Answer a general knowledge question — NOT a search of user's notes."""
    query = classified.get("query") or original_text

    answer_text = await answers.answer_general(query)
    classified["spoken_response"] = answer_text

    return {"query": query, "answer": answer_text}


async def _handle_greeting(classified: dict, original_text: str, context: dict) -> dict:
    """Conversational response. No data operations."""
    # spoken_response already set by the LLM — nothing to save
    return {}


async def _handle_switch_workspace(classified: dict, original_text: str, context: dict) -> dict:
    target = classified.get("workspace")

    if not target:
        classified["spoken_response"] = "Which workspace should I switch to?"
        return {}

    all_ws = context.get("all_workspaces", [])
    matched_name = _fuzzy_match_workspace(target, all_ws)

    ws = await sql_workspaces.switch(matched_name or target)
    note_count = await sql_notes.count(workspace_id=ws["id"])

    # Build context summary for the workspace being switched to
    context_summary = ""
    if note_count > 0:
        recent_notes = await sql_notes.list_all(workspace_id=ws["id"], limit=5)

        # Extract top tags across recent notes
        tag_freq: dict[str, int] = {}
        for n in recent_notes:
            for t in n.get("tags", []):
                if t and isinstance(t, str):
                    tag_freq[t] = tag_freq.get(t, 0) + 1
        top_tags = sorted(tag_freq.items(), key=lambda x: -x[1])[:3]

        # Build preview of what user was working on
        previews = [n["raw_text"][:40] for n in recent_notes[:2]]

        if top_tags:
            topics = ", ".join(t for t, _ in top_tags)
            context_summary = f" Topics: {topics}."

        if previews:
            last_note = previews[0]
            context_summary += f" Last note: '{last_note}'."

    # Build spoken response
    if matched_name and matched_name.lower() != target.lower():
        base = f"Switched to {ws['name']}. {note_count} notes here."
    else:
        action = "Switched to" if note_count > 0 else "Created and switched to"
        base = f"{action} {ws['name']}. {note_count} notes here."

    # Process Workspace Auto-Launch Context
    try:
        if "context_data" in ws and ws["context_data"]:
            import json
            context_data = json.loads(ws["context_data"])
            
            apps_to_open = context_data.get("apps", [])
            for app in apps_to_open:
                sys_commands.execute("open_app", {"target": app})
                
            urls_to_open = context_data.get("urls", [])
            for url in urls_to_open:
                sys_commands.execute("open_url", {"target": url})
                
            if apps_to_open or urls_to_open:
                context_summary += f" Launched {len(apps_to_open)} apps and {len(urls_to_open)} tabs."
    except Exception as e:
        print(f"[ENGINE] Failed to load workspace context: {e}")

    classified["spoken_response"] = base + context_summary

    return {"workspace": ws}


async def _handle_list_workspaces(classified: dict, original_text: str, context: dict) -> dict:
    workspaces = await sql_workspaces.list_all()

    if not workspaces:
        classified["spoken_response"] = "You only have the General workspace right now."
        return {"workspaces": []}

    names = [w["name"] for w in workspaces]
    active = next((w["name"] for w in workspaces if w.get("is_active")), "General")

    if len(names) <= 4:
        ws_text = ", ".join(names)
        classified["spoken_response"] = f"You have {len(names)} workspaces: {ws_text}. Currently in {active}."
    else:
        top = ", ".join(names[:4])
        classified["spoken_response"] = f"You have {len(names)} workspaces. Recent ones: {top}. Currently in {active}."

    return {"workspaces": workspaces}


async def _handle_list_notes(classified: dict, original_text: str, context: dict) -> dict:
    ws_id = context.get("active_workspace_id")
    ws_name = context.get("active_workspace", "General")

    notes = await sql_notes.list_all(workspace_id=ws_id, limit=5)

    if not notes:
        classified["spoken_response"] = f"No notes in {ws_name} yet."
        return {"notes": []}

    summaries = [n["raw_text"][:50] for n in notes[:3]]
    preview = ". ".join(summaries)
    total = await sql_notes.count(workspace_id=ws_id)
    classified["spoken_response"] = f"You have {total} notes in {ws_name}. Recent ones: {preview}."

    return {"notes": notes}


async def _handle_start_meeting(classified: dict, original_text: str, context: dict) -> dict:
    active_session = await sql_sessions.get_active()
    if active_session:
        classified["spoken_response"] = "You're already in a meeting. Say 'end meeting' to stop it first."
        return {"session": active_session}

    ws_id = context.get("active_workspace_id")
    session = await sql_sessions.start(workspace_id=ws_id)
    ws_name = context.get("active_workspace", "General")

    classified["spoken_response"] = f"Meeting started in {ws_name}. I'm recording everything."
    return {"session": session}


async def _handle_end_meeting(classified: dict, original_text: str, context: dict) -> dict:
    active_session = await sql_sessions.get_active()

    if not active_session:
        classified["spoken_response"] = "There's no active meeting to end."
        return {}

    transcript = await sql_sessions.get_transcript(active_session["id"])

    # Summarize
    summary_data = {"summary": "Meeting ended.", "action_items": []}
    if transcript and transcript.strip():
        try:
            summary_data = await answers.summarize(transcript)
        except Exception:
            pass

    session = await sql_sessions.end(
        active_session["id"],
        summary=summary_data.get("summary"),
        action_items=summary_data.get("action_items", []),
    )

    # Save summary as a note
    ws_id = context.get("active_workspace_id")
    action_items = summary_data.get("action_items", [])
    summary_text = summary_data.get("summary", "")

    note_text = f"Meeting Summary: {summary_text}"
    if action_items:
        note_text += "\n\nAction Items:\n" + "\n".join(f"- {item}" for item in action_items)

    note = await sql_notes.save(
        raw_text=note_text,
        tags=["meeting", "summary"],
        workspace_id=ws_id,
        source="meeting",
    )

    vector_store.add(note["id"], note["raw_text"], context.get("active_workspace", "General"), ["meeting"])

    item_count = len(action_items)
    classified["spoken_response"] = f"Meeting ended. {summary_text[:80]}. {item_count} action items found."
    return {"session": session, "summary": summary_data, "note": note}


async def _handle_pc_command(classified: dict, original_text: str, context: dict) -> dict:
    actions = classified.get("pc_actions", [])
    results = []
    calendar_events = None

    for action in actions:
        action_name = action.get("action", "")
        params = action.get("params", {})
        
        if action_name == "run_shell_command":
            from system.dynamic_commands import run_shell_command
            cmd = params.get("command", "")
            result = run_shell_command(cmd)
            results.append({"action": action_name, "result": result})
            print(f"[ENGINE] Dynamic PC Command: {cmd} → {result}")
        elif action_name == "get_calendar_events":
            from integrations.google_api import get_upcoming_calendar_events
            max_results = params.get("max_results", 5)
            # Need to await since it's an async function
            events = await get_upcoming_calendar_events(max_results)
            results.append({"action": action_name, "result": {"events": events}})
            calendar_events = events
            print(f"[ENGINE] Google API Command: get_calendar_events → {len(events)} events")
        elif action_name == "create_calendar_event":
            from integrations.google_api import create_calendar_event
            summary = params.get("summary", "New Event")
            start_time = params.get("start_time")
            end_time = params.get("end_time")
            desc = params.get("description", "")
            if start_time and end_time:
                res = await create_calendar_event(summary, start_time, end_time, desc)
                results.append({"action": action_name, "result": res})
                print(f"[ENGINE] Google API Command: create_calendar_event → {res.get('status')}")
            else:
                results.append({"action": action_name, "result": {"error": "Missing start or end time"}})
        else:
            result = sys_commands.execute(action_name, params)
            results.append({"action": action_name, "result": result})
            print(f"[ENGINE] Static PC Command: {action_name} → {result}")

    # Combine outputs if needed
    if calendar_events is not None:
        if not calendar_events:
            classified["spoken_response"] = "You have no upcoming events on your calendar."
        else:
            # Simple summarization for speech
            count = len(calendar_events)
            first_event = calendar_events[0].get("summary", "Untitled")
            classified["spoken_response"] = f"You have {count} upcoming events. The next one is {first_event}."
    else:
        # Check if we created an event
        created = next((r for r in results if r["action"] == "create_calendar_event"), None)
        if created:
            if created["result"].get("status") == "success":
                 classified["spoken_response"] = f"Created {created['result'].get('summary')} in your calendar."
            else:
                 classified["spoken_response"] = f"Failed to create event: {created['result'].get('message', 'Unknown error')}."
        else:
            outputs = [r.get("result", {}).get("output", "") for r in results if isinstance(r.get("result"), dict) and r.get("result", {}).get("output")]
            if outputs:
                summary = " ".join(outputs)[:80]
                if summary:
                     classified["spoken_response"] = f"Command executed. Output preview: {summary}"

    return {"pc_results": results}


# ═══════════════════════════════════════════════════
#  FUZZY WORKSPACE MATCHING
# ═══════════════════════════════════════════════════

def _fuzzy_match_workspace(target: str, workspaces: list[dict]) -> str | None:
    """
    Find the best workspace match.
    Steps: exact → substring → word overlap → difflib similarity.
    """
    if not workspaces:
        return None

    target_lower = target.lower().strip()

    # 1. Exact match (case-insensitive)
    for ws in workspaces:
        if ws["name"].lower() == target_lower:
            return ws["name"]

    # 2. Substring: target inside workspace name
    for ws in workspaces:
        if target_lower in ws["name"].lower():
            return ws["name"]

    # 3. Reverse substring: workspace name inside target
    for ws in workspaces:
        if ws["name"].lower() in target_lower:
            return ws["name"]

    # 4. Word overlap
    target_words = set(target_lower.split())
    best_overlap_match = None
    best_overlap = 0
    for ws in workspaces:
        ws_words = set(ws["name"].lower().split())
        overlap = len(target_words & ws_words)
        if overlap > best_overlap:
            best_overlap = overlap
            best_overlap_match = ws["name"]

    if best_overlap > 0:
        return best_overlap_match

    # 5. Fuzzy similarity (catches typos: "haackathon" → "Hackathon Project")
    best_ratio = 0.0
    best_fuzzy = None
    for ws in workspaces:
        ratio = SequenceMatcher(None, target_lower, ws["name"].lower()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_fuzzy = ws["name"]

    if best_ratio >= 0.55:
        return best_fuzzy

    return None


# ═══════════════════════════════════════════════════
#  ERROR BUFFER
# ═══════════════════════════════════════════════════

def _add_to_buffer(text: str, context: dict, note_id: str):
    """Store a failed input for later reprocessing."""
    if len(_error_buffer) >= _MAX_BUFFER_SIZE:
        _error_buffer.pop(0)
    _error_buffer.append({
        "text": text,
        "workspace_id": context.get("active_workspace_id"),
        "note_id": note_id,
        "timestamp": datetime.now().isoformat(),
    })
    print(f"[ENGINE] Buffered failed input ({len(_error_buffer)}/{_MAX_BUFFER_SIZE})")


async def process_buffer() -> list[dict]:
    """
    Retry processing buffered error items.
    Call explicitly when the system is idle — never runs automatically.
    On success: runs the correct handler and deletes the placeholder note.
    On failure: leaves the item in the buffer for next attempt.
    """
    if not _error_buffer:
        return []

    results = []
    to_remove = []

    for i, item in enumerate(_error_buffer):
        try:
            context = await _build_context()
            classified = await intents.classify(item["text"], context=context)

            if classified["confidence"] < settings.CONFIDENCE_MIN:
                continue  # Still not confident, leave in buffer

            if classified["intent"] == "create_note":
                # It really is a note — update the placeholder with proper tags
                if item.get("note_id"):
                    await sql_notes.update(item["note_id"], tags=classified.get("tags", []))
            else:
                # Different intent — run the correct handler, delete placeholder
                handler = INTENT_HANDLERS.get(classified["intent"])
                if handler:
                    await handler(classified, item["text"], context)

                if item.get("note_id"):
                    try:
                        await sql_notes.delete(item["note_id"])
                        vector_store.delete(item["note_id"])
                    except Exception:
                        pass

            to_remove.append(i)
            results.append(classified)

        except Exception:
            continue

    for i in reversed(to_remove):
        _error_buffer.pop(i)

    if results:
        print(f"[ENGINE] Buffer: processed {len(results)} items, {len(_error_buffer)} remaining")

    return results


def get_buffer_status() -> dict:
    """Check buffer state without processing. Useful for UI badges."""
    return {
        "count": len(_error_buffer),
        "items": [
            {"text": item["text"][:60], "timestamp": item["timestamp"]}
            for item in _error_buffer
        ],
    }


async def _handle_adaptive_agent(classified: dict, original_text: str, context: dict) -> dict:
    from ai import provider
    from system.dynamic_commands import GET_DYNAMIC_TOOLS
    import json

    prompt = f"""You are the Adaptive Agent for Sense, helping the user with complex, multi-step tasks.
You have access to their full workspace context and PC tools.

User Request: {original_text}

Context:
- Active Workspace: {context.get('active_workspace')}
- Recent Notes: {context.get('recent_notes')}
- Profile: {context.get('user_profile')}

Fulfill the user's request. You may call tools if necessary (e.g. to run shell commands or calendar events). If you don't need tools, just provide a helpful, conversational response. Please be concise."""

    try:
        raw = await provider.ask(
            prompt,
            temperature=0.3,
            json_mode=False,
            tools=GET_DYNAMIC_TOOLS,
            tool_choice="auto"
        )
        
        # Check if the LLM output tool calls
        if raw and raw.strip().startswith("[") and ("function" in raw or "name" in raw):
            try:
                tool_calls = json.loads(raw)
                results = []
                for tc in tool_calls:
                    if "function" in tc:
                        func = tc.get("function")
                        func_name = func.get("name")
                        args = json.loads(func.get("arguments", "{}"))
                        
                        if func_name == "run_shell_command":
                            from system.dynamic_commands import run_shell_command
                            res = run_shell_command(args.get("command", ""))
                            results.append(f"Ran command. Output: {res}")
                        elif func_name == "create_calendar_event":
                            from integrations.google_api import create_calendar_event
                            res = await create_calendar_event(
                                args.get("summary", ""),
                                args.get("start_time", ""),
                                args.get("end_time", ""),
                                args.get("description", "")
                            )
                            results.append(f"Created event: {res}")
                            
                classified["spoken_response"] = "I executed that complex task for you."
                return {"agent_results": results}
            except Exception as parsed_e:
                print(f"[ENGINE] Tool parsing error in adaptive agent: {parsed_e}")
                
        # Just return the text response
        classified["spoken_response"] = raw[:200]
        return {"agent_response": raw}
        
    except Exception as e:
        print(f"[ENGINE] Adaptive Agent failed: {e}")
        classified["spoken_response"] = "I tried to figure that out, but ran into an issue."
        return {"error": str(e)}


# ═══════════════════════════════════════════════════
#  HANDLER REGISTRY
# ═══════════════════════════════════════════════════

INTENT_HANDLERS = {
    "create_note": _handle_create_note,
    "update_note": _handle_update_note,
    "query_notes": _handle_query_notes,
    "delete_note": _handle_delete_note,
    "general_query": _handle_general_query,
    "greeting": _handle_greeting,
    "switch_workspace": _handle_switch_workspace,
    "list_workspaces": _handle_list_workspaces,
    "list_notes": _handle_list_notes,
    "start_meeting": _handle_start_meeting,
    "end_meeting": _handle_end_meeting,
    "pc_command": _handle_pc_command,
    "adaptive_agent": _handle_adaptive_agent,
}