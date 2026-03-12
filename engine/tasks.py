# Background async work (edge computation)

class Task:
    def delay(self, *args, **kwargs):
        # In a real system, this would push to a queue (Celery/Redis)
        print(f"Task queued: {self.__class__.__name__} with args {args}")
        self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        raise NotImplementedError

class ComputeEdgesTask(Task):
    def run(self, note_content: str):
        # Find related notes and create edges
        print(f"Computing edges for note: {note_content[:20]}...")
        # ai.relate(...)
        pass

compute_edges = ComputeEdgesTask()
