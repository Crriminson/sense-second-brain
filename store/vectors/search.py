import chromadb
from config import settings
import uuid

# Lazy initialization
_client = None
_collection = None

def get_collection():
    global _client, _collection
    if _collection is None:
        if _client is None:
             _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        
        # Lazy import to speed up startup
        from chromadb.utils import embedding_functions
        
        embedding_func = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        _collection = _client.get_or_create_collection(
            name="sense_memory",
            embedding_function=embedding_func
        )
    return _collection

def add(text: str, metadata: dict, id: str = None):
    collection = get_collection()
    if id is None:
        id = str(uuid.uuid4())
    
    print(f"Adding to vector store: {text[:20]}...")
    collection.add(
        documents=[text],
        metadatas=[metadata],
        ids=[id]
    )
    return id

def search(query: str, top_k: int = 5):
    collection = get_collection()
    print(f"Searching vector store for: {query}")
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )
    # Format results
    # results is a dict with lists of lists
    formatted_results = []
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            formatted_results.append({
                "content": doc,
                "metadata": results['metadatas'][0][i],
                "id": results['ids'][0][i],
                "distance": results['distances'][0][i] if results['distances'] else None
            })
    return formatted_results

def delete(id: str):
    print(f"Deleting from vector store: {id}")
    collection = get_collection()
    collection.delete(ids=[id])

