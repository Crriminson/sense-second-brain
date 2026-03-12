"""
User learning profile.

Tracks patterns across interactions so the intent prompt gets smarter over time.
Single-user system — one profile row, updated after every interaction.

Called by pipeline:
  - update_from_interaction(tags, workspace_name)  → after every process_text
  - get_profile_string()                           → during _build_context
"""

import json
from datetime import datetime
from .connection import get_db


_PROFILE_ID = "default"
_table_ready = False


# ═══════════════════════════════════════════════════
#  TABLE SETUP (lazy — runs once on first call)
# ═══════════════════════════════════════════════════

async def _ensure_table():
    global _table_ready
    if _table_ready:
        return

    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id TEXT PRIMARY KEY,
                topic_counts TEXT DEFAULT '{}',
                workspace_usage TEXT DEFAULT '{}',
                interaction_count INTEGER DEFAULT 0,
                last_active TEXT,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()

        # Insert default row if missing
        cursor = await db.execute(
            "SELECT id FROM user_profile WHERE id = ?", (_PROFILE_ID,)
        )
        if not await cursor.fetchone():
            now = datetime.now().isoformat()
            await db.execute(
                "INSERT INTO user_profile (id, created_at) VALUES (?, ?)",
                (_PROFILE_ID, now)
            )
            await db.commit()

    _table_ready = True


# ═══════════════════════════════════════════════════
#  UPDATE — called after every interaction
# ═══════════════════════════════════════════════════

async def update_from_interaction(
    tags: list[str],
    workspace_name: str,
) -> None:
    """
    Learn from one interaction. Lightweight — just counter increments.
    Never throws to caller. If it fails, the pipeline keeps going.
    """
    await _ensure_table()

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT topic_counts, workspace_usage, interaction_count FROM user_profile WHERE id = ?",
                (_PROFILE_ID,)
            )
            row = await cursor.fetchone()
            if not row:
                return

            # Parse existing counts
            try:
                topic_counts = json.loads(row["topic_counts"] or "{}")
            except json.JSONDecodeError:
                topic_counts = {}

            try:
                workspace_usage = json.loads(row["workspace_usage"] or "{}")
            except json.JSONDecodeError:
                workspace_usage = {}

            interaction_count = row["interaction_count"] or 0

            # Update topic counts from tags
            for tag in tags:
                tag = tag.strip().lower()
                if tag and len(tag) > 1:
                    topic_counts[tag] = topic_counts.get(tag, 0) + 1

            # Cap topics at 50 entries — drop least frequent
            if len(topic_counts) > 50:
                sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
                topic_counts = dict(sorted_topics[:50])

            # Update workspace usage
            ws = workspace_name.strip()
            if ws:
                workspace_usage[ws] = workspace_usage.get(ws, 0) + 1

            interaction_count += 1
            now = datetime.now().isoformat()

            await db.execute(
                """UPDATE user_profile
                   SET topic_counts = ?, workspace_usage = ?,
                       interaction_count = ?, last_active = ?
                   WHERE id = ?""",
                (
                    json.dumps(topic_counts),
                    json.dumps(workspace_usage),
                    interaction_count,
                    now,
                    _PROFILE_ID,
                )
            )
            await db.commit()

    except Exception as e:
        print(f"[PROFILE] Update failed (non-critical): {e}")


# ═══════════════════════════════════════════════════
#  READ — compact string injected into intent prompt
# ═══════════════════════════════════════════════════

async def get_profile_string() -> str:
    """
    Return a short profile summary for the intent prompt.
    Designed to add context without burning too many tokens.

    Example output:
      "42 interactions. Top topics: api (12), design (8), auth (5).
       Most used workspace: Hackathon Project (60%)."
    """
    await _ensure_table()

    try:
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT topic_counts, workspace_usage, interaction_count FROM user_profile WHERE id = ?",
                (_PROFILE_ID,)
            )
            row = await cursor.fetchone()
            if not row:
                return ""

            interaction_count = row["interaction_count"] or 0
            if interaction_count < 3:
                return ""  # Not enough data to be useful

            parts = [f"{interaction_count} interactions."]

            # Top topics
            try:
                topic_counts = json.loads(row["topic_counts"] or "{}")
            except json.JSONDecodeError:
                topic_counts = {}

            if topic_counts:
                sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
                top = sorted_topics[:5]
                topic_str = ", ".join(f"{t} ({c})" for t, c in top)
                parts.append(f"Top topics: {topic_str}.")

            # Workspace usage
            try:
                workspace_usage = json.loads(row["workspace_usage"] or "{}")
            except json.JSONDecodeError:
                workspace_usage = {}

            if workspace_usage:
                total_usage = sum(workspace_usage.values())
                if total_usage > 0:
                    sorted_ws = sorted(workspace_usage.items(), key=lambda x: -x[1])
                    top_ws_name, top_ws_count = sorted_ws[0]
                    pct = round((top_ws_count / total_usage) * 100)
                    parts.append(f"Most used workspace: {top_ws_name} ({pct}%).")

            return " ".join(parts)

    except Exception as e:
        print(f"[PROFILE] Read failed: {e}")
        return ""


# ═══════════════════════════════════════════════════
#  RAW ACCESS — for debug / API endpoints
# ═══════════════════════════════════════════════════

async def get_raw() -> dict:
    """Full profile data for debugging or API display."""
    await _ensure_table()

    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM user_profile WHERE id = ?", (_PROFILE_ID,)
        )
        row = await cursor.fetchone()
        if not row:
            return {}

        d = dict(row)
        try:
            d["topic_counts"] = json.loads(d["topic_counts"] or "{}")
        except json.JSONDecodeError:
            d["topic_counts"] = {}
        try:
            d["workspace_usage"] = json.loads(d["workspace_usage"] or "{}")
        except json.JSONDecodeError:
            d["workspace_usage"] = {}
        return d


async def reset() -> None:
    """Wipe learning data. For testing."""
    await _ensure_table()

    async with get_db() as db:
        now = datetime.now().isoformat()
        await db.execute(
            """UPDATE user_profile
               SET topic_counts = '{}', workspace_usage = '{}',
                   interaction_count = 0, last_active = ?
               WHERE id = ?""",
            (now, _PROFILE_ID)
        )
        await db.commit()