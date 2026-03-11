# database/crud.py
import uuid
import json
from datetime import datetime
from typing import Optional
from .connection import get_db


# ═══════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════

def _parse_tags(raw: str) -> list[str]:
    try:
        return json.loads(raw) if raw else []
    except json.JSONDecodeError:
        return []


def _parse_actions(raw: str) -> list[str]:
    try:
        return json.loads(raw) if raw else []
    except json.JSONDecodeError:
        return []


def _note_from_row(row) -> dict:
    d = dict(row)
    d["tags"] = _parse_tags(d.get("tags", "[]"))
    return d


def _session_from_row(row) -> dict:
    d = dict(row)
    d["action_items"] = _parse_actions(d.get("action_items", "[]"))
    return d


# ═══════════════════════════════════════
#  WORKSPACES
# ═══════════════════════════════════════

async def get_active_workspace() -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM workspaces WHERE is_active = 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def list_workspaces() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM workspaces ORDER BY is_active DESC, created_at DESC"
        )
        return [dict(r) for r in await cursor.fetchall()]


async def switch_workspace(name: str) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()

        await db.execute("UPDATE workspaces SET is_active = 0")

        cursor = await db.execute(
            "SELECT * FROM workspaces WHERE LOWER(name) = LOWER(?)",
            (name.strip(),)
        )
        row = await cursor.fetchone()

        if row:
            ws_id = row["id"]
            await db.execute(
                "UPDATE workspaces SET is_active = 1 WHERE id = ?",
                (ws_id,)
            )
        else:
            ws_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO workspaces (id, name, is_active, created_at) VALUES (?, ?, 1, ?)",
                (ws_id, name.strip(), now)
            )

        await db.commit()

        cursor = await db.execute(
            "SELECT * FROM workspaces WHERE id = ?", (ws_id,)
        )
        return dict(await cursor.fetchone())


async def delete_workspace(workspace_id: str) -> bool:
    async with get_db() as db:
        # Clean up edges that reference notes in this workspace
        await db.execute("""
            DELETE FROM edges WHERE source_id IN
            (SELECT id FROM notes WHERE workspace_id = ?)
            OR target_id IN
            (SELECT id FROM notes WHERE workspace_id = ?)
        """, (workspace_id, workspace_id))
        await db.execute(
            "DELETE FROM notes WHERE workspace_id = ?", (workspace_id,)
        )
        await db.execute(
            "DELETE FROM sessions WHERE workspace_id = ?", (workspace_id,)
        )
        cursor = await db.execute(
            "DELETE FROM workspaces WHERE id = ?", (workspace_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


# ═══════════════════════════════════════
#  NOTES
# ═══════════════════════════════════════

async def save_note(
    raw_text: str,
    tags: list[str] = [],
    summary: str = None,
    workspace_id: str = None,
    source: str = "voice",
) -> dict:
    async with get_db() as db:
        note_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Resolve workspace
        ws_name = ""
        if workspace_id:
            cursor = await db.execute(
                "SELECT name FROM workspaces WHERE id = ?", (workspace_id,)
            )
            row = await cursor.fetchone()
            if not row:
                raise ValueError(f"Workspace {workspace_id} not found")
            ws_name = row["name"]
        else:
            cursor = await db.execute(
                "SELECT id, name FROM workspaces WHERE is_active = 1"
            )
            row = await cursor.fetchone()
            if not row:
                raise ValueError("No active workspace")
            workspace_id = row["id"]
            ws_name = row["name"]

        await db.execute(
            """INSERT INTO notes
               (id, workspace_id, raw_text, summary, tags, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (note_id, workspace_id, raw_text, summary,
             json.dumps(tags), source, now)
        )
        await db.commit()

        return {
            "id": note_id,
            "workspace_id": workspace_id,
            "workspace_name": ws_name,
            "raw_text": raw_text,
            "summary": summary,
            "tags": tags,
            "source": source,
            "created_at": now,
        }


async def get_note(note_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT n.*, w.name as workspace_name
               FROM notes n JOIN workspaces w ON w.id = n.workspace_id
               WHERE n.id = ?""",
            (note_id,)
        )
        row = await cursor.fetchone()
        return _note_from_row(row) if row else None


async def list_notes(
    workspace_id: str = None,
    limit: int = 50,
) -> list[dict]:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name
                   FROM notes n JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.workspace_id = ?
                   ORDER BY n.created_at DESC LIMIT ?""",
                (workspace_id, limit)
            )
        else:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name
                   FROM notes n JOIN workspaces w ON w.id = n.workspace_id
                   ORDER BY n.created_at DESC LIMIT ?""",
                (limit,)
            )
        return [_note_from_row(r) for r in await cursor.fetchall()]


async def delete_note(note_id: str) -> bool:
    async with get_db() as db:
        await db.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?",
            (note_id, note_id)
        )
        cursor = await db.execute(
            "DELETE FROM notes WHERE id = ?", (note_id,)
        )
        await db.commit()
        return cursor.rowcount > 0


async def count_notes(workspace_id: str = None) -> int:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                "SELECT COUNT(*) as c FROM notes WHERE workspace_id = ?",
                (workspace_id,)
            )
        else:
            cursor = await db.execute("SELECT COUNT(*) as c FROM notes")
        row = await cursor.fetchone()
        return row["c"]


# ═══════════════════════════════════════
#  SESSIONS
# ═══════════════════════════════════════

async def start_session(workspace_id: str = None) -> dict:
    async with get_db() as db:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        if not workspace_id:
            cursor = await db.execute(
                "SELECT id FROM workspaces WHERE is_active = 1"
            )
            row = await cursor.fetchone()
            if not row:
                raise ValueError("No active workspace")
            workspace_id = row["id"]

        await db.execute(
            """INSERT INTO sessions
               (id, workspace_id, status, transcript, started_at)
               VALUES (?, ?, 'active', '', ?)""",
            (session_id, workspace_id, now)
        )
        await db.commit()

        return {
            "id": session_id,
            "workspace_id": workspace_id,
            "status": "active",
            "transcript": "",
            "started_at": now,
        }


async def append_transcript(session_id: str, chunk: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            """UPDATE sessions
               SET transcript = transcript || ?
               WHERE id = ? AND status = 'active'""",
            (chunk + " ", session_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def end_session(
    session_id: str,
    summary: str = None,
    action_items: list[str] = None,
) -> dict | None:
    async with get_db() as db:
        now = datetime.now().isoformat()
        sets = ["status = 'ended'", "ended_at = ?"]
        params: list = [now]

        if summary:
            sets.append("summary = ?")
            params.append(summary)
        if action_items:
            sets.append("action_items = ?")
            params.append(json.dumps(action_items))

        params.append(session_id)
        await db.execute(
            f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?",
            params
        )
        await db.commit()

    return await get_session(session_id)


async def get_session(session_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        row = await cursor.fetchone()
        return _session_from_row(row) if row else None


async def get_active_session() -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT * FROM sessions
               WHERE status = 'active'
               ORDER BY started_at DESC LIMIT 1"""
        )
        row = await cursor.fetchone()
        return _session_from_row(row) if row else None


# ═══════════════════════════════════════
#  EDGES
# ═══════════════════════════════════════

async def save_edge(
    source_id: str,
    target_id: str,
    rel_type: str,
    weight: float = 0.5,
    explanation: str = "",
) -> dict | None:
    async with get_db() as db:
        # No duplicates
        cursor = await db.execute(
            "SELECT id FROM edges WHERE source_id = ? AND target_id = ?",
            (source_id, target_id)
        )
        if await cursor.fetchone():
            return None

        edge_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        await db.execute(
            """INSERT INTO edges
               (id, source_id, target_id, rel_type, weight, explanation, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (edge_id, source_id, target_id, rel_type, weight, explanation, now)
        )
        await db.commit()

        return {
            "id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "rel_type": rel_type,
            "weight": weight,
            "explanation": explanation,
        }


async def get_edges(note_id: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT e.*,
                      s.raw_text as source_text,
                      s.summary as source_summary,
                      t.raw_text as target_text,
                      t.summary as target_summary
               FROM edges e
               JOIN notes s ON s.id = e.source_id
               JOIN notes t ON t.id = e.target_id
               WHERE e.source_id = ? OR e.target_id = ?
               ORDER BY e.weight DESC""",
            (note_id, note_id)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_graph(workspace_id: str = None) -> dict:
    async with get_db() as db:
        # ── Nodes ──
        if workspace_id:
            cursor = await db.execute(
                """SELECT n.id, n.raw_text, n.summary, n.tags,
                          n.workspace_id, n.created_at,
                          w.name as workspace_name
                   FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.workspace_id = ?""",
                (workspace_id,)
            )
        else:
            cursor = await db.execute(
                """SELECT n.id, n.raw_text, n.summary, n.tags,
                          n.workspace_id, n.created_at,
                          w.name as workspace_name
                   FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id"""
            )

        note_rows = await cursor.fetchall()
        node_ids = set()
        nodes = []

        for r in note_rows:
            node_ids.add(r["id"])
            nodes.append({
                "id": r["id"],
                "label": r["summary"] or r["raw_text"][:50],
                "workspace": r["workspace_name"],
                "tags": _parse_tags(r["tags"]),
            })

        # ── Edges ──
        edges = []
        if node_ids:
            placeholders = ",".join("?" * len(node_ids))
            ids = list(node_ids)
            cursor = await db.execute(
                f"""SELECT source_id, target_id, rel_type, weight, explanation
                    FROM edges
                    WHERE source_id IN ({placeholders})
                    AND target_id IN ({placeholders})""",
                ids + ids
            )
            edges = [dict(row) for row in await cursor.fetchall()]

        return {"nodes": nodes, "edges": edges}
