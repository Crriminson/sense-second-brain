# test_store.py
import asyncio
import os
import shutil
from store.sql import connection, workspaces, notes, sessions, edges
from config import DB_PATH

async def test_store():
    print("=" * 50)
    print("TESTING STORE MODULE (AIOSQLITE)")
    print("=" * 50)
    
    # Clean up
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed old DB: {DB_PATH}")

    # 1. Initialize DB
    print("\n[1] Initializing Database...")
    await connection.init_db()
    
    # 2. Workspaces
    print("\n[2] Testing Workspaces...")
    ws_list = await workspaces.list_all()
    print(f"  Initial workspaces: {len(ws_list)}")
    
    new_ws = await workspaces.create("Project X")
    print(f"  Created workspace: {new_ws['name']} (ID: {new_ws['id']})")
    
    switched = await workspaces.switch("Project X")
    print(f"  Switched to: {switched['name']} (Active: {switched['is_active']})")
    
    active = await workspaces.get_active()
    assert active['id'] == new_ws['id']
    print("  Verified active workspace.")

    # 3. Notes
    print("\n[3] Testing Notes...")
    note1 = await notes.save("This is a meeting note about databases.", tags=["tech", "db"])
    print(f"  Saved note 1: {note1['id']}")
    
    note2 = await notes.save("Use aiosqlite for async support.", tags=["tech", "async"])
    print(f"  Saved note 2: {note2['id']}")
    
    all_notes = await notes.list_all(active['id'])
    print(f"  Listed {len(all_notes)} notes in workspace.")
    
    search_res = await notes.search_text("aiosqlite", active['id'])
    print(f"  Search 'aiosqlite' found {len(search_res)} results.")
    assert len(search_res) == 1

    # 4. Sessions
    print("\n[4] Testing Sessions...")
    sess = await sessions.start(active['id'])
    print(f"  Started session: {sess['id']}")
    
    await sessions.append_transcript(sess['id'], "User: Hello computer.")
    await sessions.append_transcript(sess['id'], "Computer: Hello user.")
    
    transcript = await sessions.get_transcript(sess['id'])
    print(f"  Transcript length: {len(transcript)}")
    
    ended = await sessions.end(sess['id'], summary="A short chat.", action_items=["Buy milk"])
    print(f"  Ended session. Status: {ended['status']}")
    print(f"  Action items: {ended['action_items']}")

    # 5. Edges
    print("\n[5] Testing Edges...")
    edge = await edges.save(note1['id'], note2['id'], "related_to", 0.8, "Both about tech")
    print(f"  Created edge: {edge['id']} ({edge['rel_type']})")
    
    rel_notes = await edges.get_for_note(note1['id'])
    print(f"  Note 1 has {len(rel_notes)} edges.")
    assert len(rel_notes) == 1
    
    graph = await edges.get_graph(active['id'])
    print(f"  Graph has {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")

    # 6. Stats
    stats = await edges.get_stats()
    print(f"\n[6] Stats: {stats}")

    print("\n✅ STORE VERIFICATION COMPLETE")

if __name__ == "__main__":
    asyncio.run(test_store())
