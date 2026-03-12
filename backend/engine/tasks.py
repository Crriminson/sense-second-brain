# engine/tasks.py
import asyncio
from ai import relations
from store.vectors import search as vector_search
from store.sql import notes as sql_notes, edges as sql_edges
import uuid
from datetime import datetime

class Task:
    def delay(self, *args, **kwargs):
        # In a real system, this would push to a queue (Celery/Redis)
        # Here we use asyncio.create_task for a simple local background simulation
        print(f"[TASK] Queued: {self.__class__.__name__}")
        asyncio.create_task(self.run(*args, **kwargs))

    async def run(self, *args, **kwargs):
        raise NotImplementedError

class ComputeEdgesTask(Task):
    async def run(self, note_content: str):
        """
        Background task to find relationships between a new note 
        and existing knowledge.
        """
        print(f"[TASK] Computing edges for note: {note_content[:30]}...")
        
        # 1. Find contextually similar notes (top 3)
        # We skip the most recent one (itself) by potentially taking 4 and slicing
        similar_notes = vector_search(note_content, top_k=4)
        
        # 2. Compare with existing notes
        for other in similar_notes:
            # Skip if it's basically the same text (itself)
            if other["text"] == note_content:
                continue
            
            # Use AI to classify the relationship
            rel = await relations.classify(other["text"], note_content)
            
            if rel["rel_type"] != "none":
                print(f"[TASK] Found relationship: {rel['rel_type']} ({rel['weight']})")
                
                # We need the source/target IDs. 
                # Note: This is simplified; in a production app we'd pass IDs to the task.
                # For now, let's assume we can find the note by text or it was recently saved.
                
                # Save the edge to SQL
                # We need source_id and target_id.
                # Assuming 'other' has an ID from vector search.
                # We'd need the ID of the note we just saved too.
                pass

compute_edges = ComputeEdgesTask()
