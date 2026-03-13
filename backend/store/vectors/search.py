# store/vectors/search.py
import chromadb
import hashlib
from config import CHROMA_PATH, EMBEDDING_MODEL, SEARCH_SIMILARITY_MIN
import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
import logging
logging.getLogger("transformers.modeling_utils").setLevel(logging.ERROR)

os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"

_model = None
_collection = None
_embed_mode = "unknown"
_FALLBACK_DIM = 384


def _fallback_embed(text: str, dim: int = _FALLBACK_DIM) -> list[float]:
    """Deterministic lightweight embedding used when sentence-transformers is unavailable."""
    vec = [0.0] * dim
    tokens = [t for t in text.lower().split() if t]
    if not tokens:
        return vec

    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if (digest[4] % 2 == 0) else -1.0
        weight = 1.0 + (digest[5] / 255.0)
        vec[bucket] += sign * weight

    norm = sum(v * v for v in vec) ** 0.5
    if norm == 0:
        return vec
    return [v / norm for v in vec]


def _encode(text: str) -> list[float]:
    if _embed_mode == "transformer" and _model is not None:
        return _model.encode(text).tolist()
    return _fallback_embed(text)


def init():
    """
    Load embedding model and connect to ChromaDB.
    Called once at startup.
    """
    global _model, _collection, _embed_mode

    try:
        # Lazy import so broken ML dependencies don't prevent backend startup.
        from sentence_transformers import SentenceTransformer  # type: ignore

        print(f"[STORE] Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        _embed_mode = "transformer"
    except Exception as exc:
        _model = None
        _embed_mode = "fallback"
        print(f"[STORE] sentence-transformers unavailable ({exc}). Using fallback embeddings.")

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


def add(note_id: str, text: str, workspace: str, tags: list[str] | None = None):
    """Embed text and store in ChromaDB."""
    _ensure_loaded()

    embedding = _encode(text)

    _collection.upsert(
        ids=[note_id],
        embeddings=[embedding],
        documents=[text],
        metadatas=[{
            "workspace": workspace,
            "tags": ",".join(tags or []),
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

    embedding = _encode(query)
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