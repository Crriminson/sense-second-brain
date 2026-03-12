"""
Background tasks for post-processing.
Runs AFTER the main pipeline returns — never blocks the user response.

Currently one task: ComputeEdgesTask
  - Finds relationships between a new note and existing notes
  - Saves edges to SQL for the knowledge graph
"""

import asyncio
from store import vectors as vector_store
from store.sql import edges as sql_edges
from config import settings


class Task:
    """Base class for background tasks."""

    def delay(self, *args, **kwargs):
        """Queue the task to run in the background."""
        print(f"[TASK] Queued: {self.__class__.__name__}")
        asyncio.create_task(self._safe_run(*args, **kwargs))

    async def _safe_run(self, *args, **kwargs):
        """Wrapper that catches ALL errors — a failed task never crashes the server."""
        try:
            await self.run(*args, **kwargs)
        except Exception as e:
            print(f"[TASK] {self.__class__.__name__} failed: {e}")

    async def run(self, *args, **kwargs):
        raise NotImplementedError


class ComputeEdgesTask(Task):
    async def run(self, note_content: str, note_id: str):
        """
        Find relationships between a new note and existing notes.
        
        Pipeline calls: compute_edges.delay(note["raw_text"], note["id"])
        So this receives: (note_content: str, note_id: str)
        """
        print(f"[TASK] Computing edges for: {note_content[:40]}...")

        # Find similar notes in vector store
        try:
            similar = vector_store.search(note_content, top_k=5)
        except Exception as e:
            print(f"[TASK] Vector search failed: {e}")
            return

        if not similar:
            print(f"[TASK] No similar notes found. Skipping edges.")
            return

        edges_created = 0

        for other in similar:
            # Skip self
            if other["id"] == note_id:
                continue

            # Skip low similarity
            similarity = other.get("similarity", 0)
            if similarity < settings.EDGE_SIMILARITY_MIN:
                continue

            try:
                # Lazy import — relations module may not always be needed
                from ai import relations

                rel = await relations.classify(note_content, other["text"])

                if not rel or rel.get("rel_type") == "none":
                    continue

                weight = rel.get("weight", 0.5)
                if weight < 0.3:
                    continue

                result = await sql_edges.save(
                    source_id=note_id,
                    target_id=other["id"],
                    rel_type=rel["rel_type"],
                    weight=weight,
                    explanation=rel.get("explanation", ""),
                )

                if result:
                    edges_created += 1
                    print(
                        f"[TASK] Edge: {note_content[:20]} "
                        f"--[{rel['rel_type']}]--> "
                        f"{other['text'][:20]} "
                        f"(weight: {weight})"
                    )

            except Exception as e:
                print(f"[TASK] Edge classification failed for '{other['text'][:30]}': {e}")
                continue

        print(f"[TASK] Done. {edges_created} edges created for: {note_content[:40]}")


# ═══════════════════════════════════════════════════
#  SINGLETON INSTANCES — imported by pipeline
# ═══════════════════════════════════════════════════

compute_edges = ComputeEdgesTask()