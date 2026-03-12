# store/vectors/search.py
import chromadb
from sentence_transformers import SentenceTransformer
from config import CHROMA_PATH, EMBEDDING_MODEL, SEARCH_SIMILARITY_MIN

_model = None
_collection = None


def init():
    """
    Load embedding model and connect to ChromaDB.
    Called once at startup.
    """
    global _model, _collection

    print(f"[STORE] Loading embedding model: {EMBEDDING_MODEL}")
    _model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    _collection = client.get_or_create_collection(
        name="notes",
        metadata={"hnsw:space": "cosine"}
    )

    count = _collection.count()
    print(f"[STORE] Vectors ready ({count} embeddings loaded)")


def _ensure_loaded():
    """Auto-init if someone calls add/search before init()."""
    if not _model or not _collection:
        init()


def add(note_id: str, text: str, workspace: str, tags: list[str] = []):
    """Embed text and store in ChromaDB."""
    _ensure_loaded()

    embedding = _model.encode(text).tolist()

    _collection.upsert(
        ids=[note_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "workspace": workspace,
            "tags": ",".join(tags),
        }]
    )


def search(
    query: str,
    top_k: int = 5,
    workspace: str = None,
    min_similarity: float = None,
) -> list[dict]:
    """Find notes semantically similar to the query."""
    _ensure_loaded()

    if min_similarity is None:
        min_similarity = SEARCH_SIMILARITY_MIN

    embedding = _model.encode(query).tolist()
    where = {"workspace": workspace} if workspace else None

    results = _collection.query(
        query_embeddings=[embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"]
    )

    # No results
    if not results["documents"] or not results["documents"][0]:
        return []

    notes = []
    for i in range(len(results["documents"][0])):
        # Convert cosine distance to similarity
        distance = results["distances"][0][i]
        similarity = 1 - distance

        if similarity < min_similarity:
            continue

        notes.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "workspace": results["metadatas"][0][i].get("workspace", ""),
            "tags": results["metadatas"][0][i].get("tags", "").split(","),
            "similarity": round(similarity, 3),
        })

    return notes


def delete(note_id: str):
    """Remove a note's embedding from the vector store."""
    _ensure_loaded()
    try:
        _collection.delete(ids=[note_id])
    except Exception:
        pass


def count() -> int:
    """How many embeddings are stored."""
    _ensure_loaded()
    return _collection.count()