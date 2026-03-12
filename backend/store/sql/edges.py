# store/sql/edges.py
import uuid
import json
from datetime import datetime
from .connection import get_db


async def save(source_id: str, target_id: str, rel_type: str,
               weight: float = 0.5, explanation: str = "") -> dict | None:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT id FROM edges
               WHERE (source_id = ? AND target_id = ?)
               OR (source_id = ? AND target_id = ?)""",
            (source_id, target_id, target_id, source_id)
        )
        if await cursor.fetchone():
            return None
        edge_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        await db.execute(
            """INSERT INTO edges (id, source_id, target_id, rel_type, weight, explanation, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (edge_id, source_id, target_id, rel_type, weight, explanation, now)
        )
        await db.commit()
        return {
            "id": edge_id, "source_id": source_id, "target_id": target_id,
            "rel_type": rel_type, "weight": weight, "explanation": explanation,
            "created_at": now,
        }


async def update_weight(edge_id: str, weight: float, explanation: str = None) -> bool:
    async with get_db() as db:
        if explanation is not None:
            await db.execute("UPDATE edges SET weight = ?, explanation = ? WHERE id = ?",
                           (weight, explanation, edge_id))
        else:
            await db.execute("UPDATE edges SET weight = ? WHERE id = ?", (weight, edge_id))
        await db.commit()
        return True


async def get_for_note(note_id: str) -> list[dict]:
    async with get_db() as db:
        cursor = await db.execute(
            """SELECT e.*,
                      s.raw_text as source_text, s.summary as source_summary,
                      t.raw_text as target_text, t.summary as target_summary
               FROM edges e
               JOIN notes s ON s.id = e.source_id
               JOIN notes t ON t.id = e.target_id
               WHERE e.source_id = ? OR e.target_id = ?
               ORDER BY e.weight DESC""",
            (note_id, note_id)
        )
        return [dict(row) for row in await cursor.fetchall()]


async def get_contradictions(workspace_id: str = None) -> list[dict]:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                """SELECT e.*, s.raw_text as source_text, t.raw_text as target_text
                   FROM edges e
                   JOIN notes s ON s.id = e.source_id
                   JOIN notes t ON t.id = e.target_id
                   WHERE e.rel_type = 'contradicts'
                   AND (s.workspace_id = ? OR t.workspace_id = ?)
                   ORDER BY e.created_at DESC""",
                (workspace_id, workspace_id)
            )
        else:
            cursor = await db.execute(
                """SELECT e.*, s.raw_text as source_text, t.raw_text as target_text
                   FROM edges e
                   JOIN notes s ON s.id = e.source_id
                   JOIN notes t ON t.id = e.target_id
                   WHERE e.rel_type = 'contradicts'
                   ORDER BY e.created_at DESC"""
            )
        return [dict(row) for row in await cursor.fetchall()]


async def delete(edge_id: str) -> bool:
    async with get_db() as db:
        cursor = await db.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
        await db.commit()
        return cursor.rowcount > 0


async def delete_for_note(note_id: str) -> int:
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM edges WHERE source_id = ? OR target_id = ?", (note_id, note_id)
        )
        await db.commit()
        return cursor.rowcount


async def get_graph(workspace_id: str = None) -> dict:
    async with get_db() as db:
        if workspace_id:
            cursor = await db.execute(
                """SELECT n.id, n.raw_text, n.summary, n.tags, n.workspace_id,
                          n.created_at, w.name as workspace_name
                   FROM notes n JOIN workspaces w ON w.id = n.workspace_id
                   WHERE n.workspace_id = ?""", (workspace_id,)
            )
        else:
            cursor = await db.execute(
                """SELECT n.id, n.raw_text, n.summary, n.tags, n.workspace_id,
                          n.created_at, w.name as workspace_name
                   FROM notes n JOIN workspaces w ON w.id = n.workspace_id"""
            )
        note_rows = await cursor.fetchall()
        node_ids = set()
        nodes = []
        for r in note_rows:
            node_ids.add(r["id"])
            try:
                tags = json.loads(r["tags"]) if r["tags"] else []
            except json.JSONDecodeError:
                tags = []
            nodes.append({
                "id": r["id"], "label": r["summary"] or r["raw_text"][:50],
                "workspace": r["workspace_name"], "workspace_id": r["workspace_id"],
                "tags": tags, "created_at": r["created_at"],
            })
        edge_list = []
        if node_ids:
            placeholders = ",".join("?" * len(node_ids))
            ids = list(node_ids)
            cursor = await db.execute(
                f"""SELECT id, source_id, target_id, rel_type, weight, explanation
                    FROM edges
                    WHERE source_id IN ({placeholders}) AND target_id IN ({placeholders})""",
                ids + ids
            )
            for row in await cursor.fetchall():
                edge_list.append({
                    "id": row["id"], "source": row["source_id"], "target": row["target_id"],
                    "rel_type": row["rel_type"], "weight": row["weight"],
                    "explanation": row["explanation"],
                })
        return {"nodes": nodes, "edges": edge_list}


async def get_stats() -> dict:
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) as c FROM edges")
        total = (await cursor.fetchone())["c"]
        cursor = await db.execute("SELECT COUNT(*) as c FROM edges WHERE rel_type = 'contradicts'")
        contradictions = (await cursor.fetchone())["c"]
        cursor = await db.execute("SELECT COUNT(*) as c FROM edges WHERE rel_type = 'extends'")
        extensions = (await cursor.fetchone())["c"]
        cursor = await db.execute("SELECT COUNT(*) as c FROM edges WHERE rel_type = 'related_to'")
        related = (await cursor.fetchone())["c"]
        return {
            "total_edges": total, "contradictions": contradictions,
            "extensions": extensions, "related": related,
        }

