# vector/store.py
import chromadb
from sentence_transformers import SentenceTransformer

_model = None
_collection = None


def init_vector():
    global _model, _collection
    print("[VECTOR] Loading embedding model...")
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path="./chroma_data")
    _collection = client.get_or_create_collection(
        name="notes",
        metadata={"hnsw:space": "cosine"}
    )
    print("[VECTOR] Ready")


def _ensure_loaded():
    if not _model or not _collection:
        init_vector()


def add_note(note_id: str, text: str, workspace: str, tags: list[str] = []):
    """Store a note's embedding. Call after saving to SQLite."""
    _ensure_loaded()
    embedding = _model.encode(text).tolist()
    _collection.upsert(
        ids=[note_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{"workspace": workspace, "tags": ",".join(tags)}]
    )


def search(query: str, top_k: int = 5, workspace: str = None) -> list[dict]:
    """Find notes semantically similar to query text."""
    _ensure_loaded()
    embedding = _model.encode(query).tolist()
    where = {"workspace": workspace} if workspace else None

    results = _collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"][0]:
        return []

    notes = []
    for i in range(len(results["documents"][0])):
        similarity = 1 - results["distances"][0][i]
        if similarity < 0.3:
            continue
        notes.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "workspace": results["metadatas"][0][i]["workspace"],
            "similarity": round(similarity, 3),
        })
    return notes


def delete_note(note_id: str):
    """Remove note from vector index."""
    _ensure_loaded()
    try:
        _collection.delete(ids=[note_id])
    except Exception:
        pass
