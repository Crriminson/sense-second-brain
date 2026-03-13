# store/sql/workspaces.py
import uuid
from datetime import datetime
from .connection import get_db


async def get_active() -> dict | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM workspaces WHERE is_active = 1")
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_by_id(workspace_id: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_by_name(name: str) -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM workspaces WHERE LOWER(name) = LOWER(?)", (name.strip(),)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def list_all() -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM workspaces ORDER BY is_active DESC, created_at DESC"
        )
        return [dict(r) for r in await cursor.fetchall()]


async def create(name: str) -> dict:
    async with get_db() as db:
        ws_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        await db.execute(
            "INSERT INTO workspaces (id, name, is_active, created_at, context_data) VALUES (?, ?, 0, ?, ?)",
            (ws_id, name.strip(), now, "{}")
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,))
        return dict(await cursor.fetchone())


async def switch(name: str) -> dict:
    async with get_db() as db:
        now = datetime.now().isoformat()
        await db.execute("UPDATE workspaces SET is_active = 0")
        cursor = await db.execute(
            "SELECT * FROM workspaces WHERE LOWER(name) = LOWER(?)", (name.strip(),)
        )
        row = await cursor.fetchone()
        if row:
            ws_id = row["id"]
            await db.execute("UPDATE workspaces SET is_active = 1 WHERE id = ?", (ws_id,))
        else:
            ws_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO workspaces (id, name, is_active, created_at, context_data) VALUES (?, ?, 1, ?, ?)",
                (ws_id, name.strip(), now, "{}")
            )
        await db.commit()
        cursor = await db.execute("SELECT * FROM workspaces WHERE id = ?", (ws_id,))
        return dict(await cursor.fetchone())


async def delete(workspace_id: str) -> bool:
    async with get_db() as db:
        await db.execute("""
            DELETE FROM edges WHERE source_id IN
            (SELECT id FROM notes WHERE workspace_id = ?)
            OR target_id IN
            (SELECT id FROM notes WHERE workspace_id = ?)
        """, (workspace_id, workspace_id))
        await db.execute("DELETE FROM notes WHERE workspace_id = ?", (workspace_id,))
        await db.execute("DELETE FROM sessions WHERE workspace_id = ?", (workspace_id,))
        cursor = await db.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        await db.commit()

async def update_context(workspace_id: str, context_data: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "UPDATE workspaces SET context_data = ? WHERE id = ?",
            (context_data, workspace_id)
        )
        await db.commit()
        return cursor.rowcount > 0
