"""Seed the backend SQLite database with demo "messy note" content.

This is intended for hackathon/demo use: it creates workspaces and inserts a
bunch of raw, voice-style notes into the `notes` table.

Run:
    python backend/scripts/seed_demo_notes.py
"""

import asyncio
import os
import sys

# Ensure the backend package is importable when running from the repository root.
# Many backend modules import `config` as a top-level module, so we need the backend
# directory on sys.path.
# Ensure the backend directory is on sys.path so imports like `from store.sql...` resolve.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from store.sql.connection import get_db, init_db
from store.sql import workspaces, notes
from store import vectors as vector_store
from engine.tasks import compute_edges

DEMO_DATA = {
    "HackOverflow": [
        "Idea for hackathon: developers constantly switch between docs, chats, tasks, and code. That creates cognitive overload.",
        "Instead of another dashboard we should build something that captures thoughts instantly using voice.",
        "Key insight: most productivity tools require users to structure information manually which increases mental load.",
        "What if the system automatically converts voice into structured notes, tasks, and knowledge graphs?",
        "Our Android app could act like a brain extension — quick voice capture and AI organizes everything later.",
        "Need WebSocket communication so the mobile app can talk to the AI brain backend in real time.",
        "AI backend responsibilities: store notes, detect relationships, extract tasks, summarize workspaces.",
        "We should show judges how messy thoughts become structured knowledge automatically.",
        "Potential demo: capture multiple random notes during presentation and show system organizing them.",
        "System should detect things like project ideas, technical decisions, deadlines, and tasks.",
        "Example: if someone says 'we need websocket support' the system should extract a task automatically.",
        "Maybe integrate vector search so the assistant can answer questions about the workspace.",
        "Important selling point: reduces context switching and cognitive overload.",
        "Could also detect relationships between concepts like voice capture → knowledge graph → workspace insights.",
        "Future idea: integrate hardware buttons or wearable capture device for instant thought recording.",
    ],
    "RoboRush": [
        "Competition requires building both a line follower robot and a micromouse robot within one month.",
        "Line follower goal is maximum speed while maintaining stability on sharp curves.",
        "Need to experiment with PID control to stabilize the robot when turning quickly.",
        "Sensor array likely IR reflective sensors arranged in a row under the robot.",
        "Motor control needs to be extremely responsive or we lose time in corrections.",
        "We should build a calibration routine that automatically detects track contrast.",
        "Micromouse problem is basically maze solving using limited sensors.",
        "Flood fill algorithm seems to be the most commonly used strategy in competitions.",
        "Robot should first explore maze then compute shortest path for second run.",
        "Need to optimize memory usage since microcontrollers have limited RAM.",
        "Wheel encoders might help improve movement accuracy in the maze.",
        "We should test different wheel diameters to see if higher speed is achievable.",
        "Battery weight vs capacity tradeoff could affect acceleration.",
        "Maybe we can run simulations of the maze solving algorithm before implementing on hardware.",
        "Need a practice maze setup to test algorithms regularly.",
    ],
    "StudyForge": [
        "Dynamic programming solves problems where subproblems repeat many times.",
        "Need to practice recognizing DP problems quickly in coding contests.",
        "Greedy algorithms work when locally optimal choices lead to globally optimal solutions.",
        "Important graph algorithms include Dijkstra, Bellman-Ford, and A star.",
        "A star is useful for pathfinding in robotics because it combines heuristics with shortest path search.",
        "Convex optimization appears frequently in machine learning models.",
        "Simulated annealing is inspired by physical annealing processes.",
        "Genetic algorithms simulate evolution to find optimal solutions.",
        "Branch and bound can prune search trees efficiently in combinatorial optimization.",
        "Understanding time complexity is critical when selecting algorithms.",
        "Need to review NP-complete problems and reduction techniques.",
        "Divide and conquer algorithms like merge sort split problems recursively.",
        "Graph traversal algorithms like BFS and DFS are fundamental tools.",
    ],
    "Personal": [
        "I prefer capturing ideas quickly using voice because typing slows down brainstorming.",
        "When solving complex problems I try to first break them into smaller subproblems.",
        "Robotics projects interest me because they combine hardware, algorithms, and control systems.",
        "I enjoy experimenting with AI systems that augment human thinking.",
        "Hackathons are exciting because rapid prototyping often leads to creative solutions.",
        "Learning algorithms helps build better robotics navigation and planning systems.",
        "I tend to explore many ideas quickly before committing to a single approach.",
        "Need to remember to tune PID constants tomorrow.",
        "Micromouse path planning might benefit from A star instead of flood fill maybe.",
        "Idea: use voice capture during robotics testing sessions.",
        "Could HackOverflow detect tasks automatically from brainstorming?",
    ],
}


async def _note_exists(workspace_id: str, raw_text: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT 1 FROM notes WHERE workspace_id = ? AND raw_text = ? LIMIT 1",
            (workspace_id, raw_text),
        )
        return await cursor.fetchone() is not None


async def main():
    await init_db()

    print("[seed] Inserting demo notes into the database...")

    for ws_name, note_texts in DEMO_DATA.items():
        ws = await workspaces.get_by_name(ws_name)
        if not ws:
            ws = await workspaces.create(ws_name)
            print(f"[seed] Created workspace: {ws_name} (id={ws['id']})")
        else:
            print(f"[seed] Using existing workspace: {ws_name} (id={ws['id']})")

        inserted = 0
        for note_text in note_texts:
            if await _note_exists(ws["id"], note_text):
                continue
            note = await notes.save(raw_text=note_text, workspace_id=ws["id"])
            # vector_store.add(
            #     note_id=note["id"],
            #     text=note["raw_text"],
            #     workspace=ws["name"],
            #     tags=[],
            # )
            # compute_edges.delay(note["raw_text"], note["id"])
            inserted += 1

        print(f"[seed] Inserted {inserted} new notes into '{ws_name}'")

    print("[seed] Done.")


async def index_existing_notes():
    """Index all notes in the demo workspaces into vector store and compute edges."""
    print("[seed] Indexing existing notes into vector store...")

    for ws_name in DEMO_DATA.keys():
        ws = await workspaces.get_by_name(ws_name)
        if not ws:
            continue

        all_notes = await notes.list_all(workspace_id=ws["id"])
        for note in all_notes:
            # Check if already indexed? For simplicity, just add (vector store might handle duplicates)
            vector_store.add(
                note_id=note["id"],
                text=note["raw_text"],
                workspace=ws["name"],
                tags=note.get("tags", []),
            )
            compute_edges.delay(note["raw_text"], note["id"])

        print(f"[seed] Indexed {len(all_notes)} notes in '{ws_name}'")

    print("[seed] Indexing complete.")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(index_existing_notes())
