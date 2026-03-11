# database/connection.py
import aiosqlite
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

DB_PATH = "second_brain.db"


@asynccontextmanager
async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=5000")
    await db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        await db.close()


async def init_db():
    async with get_db() as db:

        await db.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                summary TEXT,
                tags TEXT DEFAULT '[]',
                source TEXT DEFAULT 'voice',
                created_at TEXT NOT NULL,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                transcript TEXT DEFAULT '',
                summary TEXT,
                action_items TEXT DEFAULT '[]',
                started_at TEXT NOT NULL,
                ended_at TEXT,
                FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                rel_type TEXT NOT NULL,
                weight REAL DEFAULT 0.5,
                explanation TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES notes(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES notes(id) ON DELETE CASCADE
            )
        """)

        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_notes_workspace ON notes(workspace_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at DESC)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)"
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)"
        )

        await db.commit()

        # Seed default workspace
        try:
            now = datetime.now().isoformat()
            await db.execute(
                "INSERT INTO workspaces (id, name, is_active, created_at) VALUES (?, ?, 1, ?)",
                (str(uuid.uuid4()), "General", now)
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            pass

    print("[DB] Ready")
