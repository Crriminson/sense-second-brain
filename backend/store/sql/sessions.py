# store/sql/sessions.py
import uuid
import json
from datetime import datetime
from .connection import get_db


def _parse(row) -> dict:
    d = dict(row)
    try:
        d["action_items"] = json.loads(d["action_items"]) if d["action_items"] else []
    except json.JSONDecodeError:
        d["action_items"] = []
    return d


async def start(workspace_id: str = None) -> dict:
    async with get_db() as db:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        if not workspace_id:
            cursor = await db.execute("SELECT id FROM workspaces WHERE is_active = 1")
            row = await cursor.fetchone()
            if not row:
                raise ValueError("No active workspace")
            workspace_id = row["id"]
        await db.execute(
            """INSERT INTO sessions (id, workspace_id, status, transcript, started_at)
               VALUES (?, ?, 'active', '', ?)""",
            (session_id, workspace_id, now)
        )
        await db.commit()
        return {
            "id": session_id, "workspace_id": workspace_id,
            "status": "active", "transcript": "",
            "summary": None, "action_items": [],
            "started_at": now, "ended_at": None,
        }


async def append_transcript(session_id: str, chunk: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            """UPDATE sessions SET transcript = transcript || ?
               WHERE id = ? AND status = 'active'""",
            (chunk + " ", session_id)
        )
        await db.commit()
        return cursor.rowcount > 0


async def end(session_id: str, summary: str = None, action_items: list[str] = None) -> dict | None:
    async with get_db() as db:
        now = datetime.now().isoformat()
        sets = ["status = 'ended'", "ended_at = ?"]
        params: list = [now]
        if summary is not None:
            sets.append("summary = ?"); params.append(summary)
        if action_items is not None:
            sets.append("action_items = ?"); params.append(json.dumps(action_items))
        params.append(session_id)
        await db.execute(f"UPDATE sessions SET {', '.join(sets)} WHERE id = ?", params)
        await db.commit()
    return await get(session_id)


async def get(session_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = await cursor.fetchone()
        return _parse(row) if row else None


async def get_active() -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE status = 'active' ORDER BY started_at DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return _parse(row) if row else None


async def list_all(workspace_id: str = None, limit: int = 20) -> list[dict]:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE workspace_id = ? ORDER BY started_at DESC LIMIT ?",
                (workspace_id, limit)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
            )
        return [_parse(r) for r in await cursor.fetchall()]


async def get_transcript(session_id: str) -> str:
    async with get_db() as db:
        cursor = await db.execute("SELECT transcript FROM sessions WHERE id = ?", (session_id,))
        row = await cursor.fetchone()
        return row["transcript"] if row else ""

