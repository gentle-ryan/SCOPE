import threading
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from google import genai
from config import GEMINI_EMBED_MODEL, OUTPUTS_DIR
from services.llm_client import LLMClient

_chroma_clients: dict[str, chromadb.PersistentClient] = {}
_chroma_lock = threading.Lock()


class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self._client: genai.Client = LLMClient.get_instance().client

    def __call__(self, input: Documents) -> Embeddings:
        result = self._client.models.embed_content(
            model=GEMINI_EMBED_MODEL,
            contents=input,
        )
        return [e.values for e in result.embeddings]


def _get_chroma_client(run_id: str) -> chromadb.PersistentClient:
    if run_id not in _chroma_clients:
        with _chroma_lock:
            if run_id not in _chroma_clients:
                db_path = str(OUTPUTS_DIR / run_id / "chroma")
                _chroma_clients[run_id] = chromadb.PersistentClient(path=db_path)
    return _chroma_clients[run_id]


def _get_collection(run_id: str) -> chromadb.Collection:
    client = _get_chroma_client(run_id)
    return client.get_or_create_collection(
        name="documents",
        embedding_function=GeminiEmbeddingFunction(),
    )


def build_retriever(run_id: str, markdown_text: str, chunk_size: int = 800) -> None:
    collection = _get_collection(run_id)
    chunks = [markdown_text[i : i + chunk_size] for i in range(0, len(markdown_text), chunk_size)]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    batch = 100
    for i in range(0, len(ids), batch):
        collection.upsert(ids=ids[i:i+batch], documents=chunks[i:i+batch])
    print(f"  ChromaDB 인덱스 구축 완료: {len(chunks)}개 청크")


def ensure_index(run_id: str, parsed_markdown: str) -> None:
    """컬렉션이 비어있으면 인덱스를 (재)구축한다."""
    collection = _get_collection(run_id)
    if collection.count() == 0:
        print("  ChromaDB 인덱스 비어있음 → 구축 중...")
        build_retriever(run_id, parsed_markdown)


def retrieve_context(run_id: str, query: str, n_results: int = 8) -> list[str]:
    collection = _get_collection(run_id)
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(n_results, count))
    return results["documents"][0] if results["documents"] else []
