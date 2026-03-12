# store/sql/notes.py
import uuid
import json
from datetime import datetime
from .connection import get_db


def _parse(row) -> dict:
    d = dict(row)
    try:
        d["tags"] = json.loads(d["tags"]) if d["tags"] else []
    except json.JSONDecodeError:
        d["tags"] = []
    return d


async def save(raw_text: str, tags: list[str] = [], summary: str = None,
               workspace_id: str = None, source: str = "voice") -> dict:
    async with get_db() as db:
        note_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        ws_name = ""
        if workspace_id:
            cursor = await db.execute("SELECT name FROM workspaces WHERE id = ?", (workspace_id,))
            row = await cursor.fetchone()
            if not row:
                raise ValueError(f"Workspace {workspace_id} not found")
            ws_name = row["name"]
        else:
            cursor = await db.execute("SELECT id, name FROM workspaces WHERE is_active = 1")
            row = await cursor.fetchone()
            if not row:
                raise ValueError("No active workspace")
            workspace_id = row["id"]
            ws_name = row["name"]
        await db.execute(
            """INSERT INTO notes (id, workspace_id, raw_text, summary, tags, source, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (note_id, workspace_id, raw_text, summary, json.dumps(tags), source, now)
        )
        await db.commit()
        return {
            "id": note_id, "workspace_id": workspace_id, "workspace_name": ws_name,
            "raw_text": raw_text, "summary": summary, "tags": tags,
            "source": source, "created_at": now,
        }


async def get(note_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT n.*, w.name as workspace_name FROM notes n
               JOIN workspaces w ON w.id = n.workspace_id WHERE n.id = ?""", (note_id,)
        )
        row = await cursor.fetchone()
        return _parse(row) if row else None


async def list_all(workspace_id: str = None, limit: int = 50) -> list[dict]:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.workspace_id = ? ORDER BY n.created_at DESC LIMIT ?""",
                (workspace_id, limit)
            )
        else:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   ORDER BY n.created_at DESC LIMIT ?""", (limit,)
            )
        return [_parse(r) for r in await cursor.fetchall()]


async def list_by_tag(tag: str, workspace_id: str = None, limit: int = 50) -> list[dict]:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.workspace_id = ? AND n.tags LIKE ?
                   ORDER BY n.created_at DESC LIMIT ?""",
                (workspace_id, f'%"{tag}"%', limit)
            )
        else:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.tags LIKE ? ORDER BY n.created_at DESC LIMIT ?""",
                (f'%"{tag}"%', limit)
            )
        return [_parse(r) for r in await cursor.fetchall()]


async def search_text(query: str, workspace_id: str = None, limit: int = 50) -> list[dict]:
    async with get_db() as db:
        pattern = f"%{query}%"
        if workspace_id:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.workspace_id = ? AND (n.raw_text LIKE ? OR n.summary LIKE ?)
                   ORDER BY n.created_at DESC LIMIT ?""",
                (workspace_id, pattern, pattern, limit)
            )
        else:
            cursor = await db.execute(
                """SELECT n.*, w.name as workspace_name FROM notes n
                   JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.raw_text LIKE ? OR n.summary LIKE ?
                   ORDER BY n.created_at DESC LIMIT ?""",
                (pattern, pattern, limit)
            )
        return [_parse(r) for r in await cursor.fetchall()]


async def update(note_id: str, raw_text: str = None, summary: str = None, tags: list[str] = None) -> dict | None:
    async with get_db() as db:
        sets = []
        params = []
        if raw_text is not None:
            sets.append("raw_text = ?"); params.append(raw_text)
        if summary is not None:
            sets.append("summary = ?"); params.append(summary)
        if tags is not None:
            sets.append("tags = ?"); params.append(json.dumps(tags))
        if not sets:
            return await get(note_id)
        params.append(note_id)
        await db.execute(f"UPDATE notes SET {', '.join(sets)} WHERE id = ?", params)
        await db.commit()
    return await get(note_id)


async def delete(note_id: str) -> bool:
    async with get_db() as db:
        await db.execute("DELETE FROM edges WHERE source_id = ? OR target_id = ?", (note_id, note_id))
        cursor = await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        await db.commit()
        return cursor.rowcount > 0


async def count(workspace_id: str = None) -> int:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                "SELECT COUNT(*) as c FROM notes WHERE workspace_id = ?", (workspace_id,)
            )
        else:
            cursor = await db.execute("SELECT COUNT(*) as c FROM notes")
        row = await cursor.fetchone()
        return row["c"]


async def get_recent(workspace_id: str, limit: int = 10) -> list[dict]:
    return await list_all(workspace_id=workspace_id, limit=limit)

