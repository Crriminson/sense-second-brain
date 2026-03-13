"""
SQL Store for Google Credentials
"""
import uuid
import time
from .connection import get_db

async def save_credentials(access_token: str, refresh_token: str, expires_at: float, email: str = ""):
    """Save or update Google OAuth credentials. We assume single-user mode for now, so we just keep one record or act as default."""
    async with get_db() as db:
        # Check if we already have credentials
        async with db.execute("SELECT id FROM google_credentials LIMIT 1") as cursor:
            row = await cursor.fetchone()
        
        if row:
            cred_id = row["id"]
            await db.execute(
                """
                UPDATE google_credentials 
                SET access_token = ?, refresh_token = COALESCE(?, refresh_token), expires_at = ?, email = ?
                WHERE id = ?
                """,
                (access_token, refresh_token, expires_at, email, cred_id)
            )
        else:
            cred_id = str(uuid.uuid4())
            await db.execute(
                """
                INSERT INTO google_credentials (id, access_token, refresh_token, expires_at, email)
                VALUES (?, ?, ?, ?, ?)
                """,
                (cred_id, access_token, refresh_token, expires_at, email)
            )
        await db.commit()
        return cred_id

async def get_credentials() -> dict | None:
    """Get the active Google credentials."""
    async with get_db() as db:
        async with db.execute("SELECT * FROM google_credentials LIMIT 1") as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None

async def delete_credentials():
    """Clear credentials on logout."""
    async with get_db() as db:
        await db.execute("DELETE FROM google_credentials")
        await db.commit()
