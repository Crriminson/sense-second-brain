# engine/pipeline.py
from ai import intents, answers
from store.sql import notes as sql_notes, workspaces as sql_workspaces
from store import vectors as vector_store
from system import commands as sys_commands
from engine.tasks import compute_edges

async def process_text(text: str) -> dict:
    """
    Takes text from the phone, runs it through AI, 
    and returns what the system should do/say.
    """
    print(f"[ENGINE] Processing: '{text}'")
    
    # 1. Get active workspace
    active_ws = await sql_workspaces.get_active()
    ws_name = active_ws["name"] if active_ws else "General"
    ws_id = active_ws["id"] if active_ws else None

    # 2. Run AI classification
    classified = await intents.classify(text, active_workspace=ws_name)
    intent = classified["intent"]
    
    print(f"[ENGINE] AI decided intent is: {intent}")

    # 3. Handle Intents
    if intent == "create_note":
        # Save to SQL
        note = await sql_notes.save(
            raw_text=classified["text"] or text,
            tags=classified["tags"],
            workspace_id=ws_id,
            source="voice"
        )
        # Save to Vector Store
        vector_store.add(
            note_id=note["id"],
            text=note["raw_text"],
            workspace=ws_name,
            tags=note["tags"]
        )
        # Trigger background relationship extraction
        compute_edges.delay(note["raw_text"])
        
    elif intent == "query_notes":
        # Search vector store for relevant context
        results = vector_store.search(classified["query"] or text, workspace=ws_name)
        # Generate synthesized answer
        answer_text = await answers.answer(classified["query"] or text, results)
        classified["spoken_response"] = answer_text

    elif intent == "pc_command":
        # Execute system actions
        for action in classified.get("pc_actions", []):
            sys_commands.execute_pc_command(action["action"], action["params"])

    print(f"[ENGINE] AI wants to say: {classified['spoken_response']}")
    
    return classified
