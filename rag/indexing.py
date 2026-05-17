from data_sources.loaders import Document
from rag.chunking import chunk_documents
from core.embeddings import EmbeddingModel
from core.vectorstore import VectorStore


def build_index(file_path):
    # 1. Load
    documents = Document.load_pubmed_text(file_path)

    # 2. Chunk
    chunks = chunk_documents(documents)

    texts = [c["content"] for c in chunks]

    # 3. Embedding
    embedder = EmbeddingModel()
    embeddings = embedder.embed(texts)

    # 4. Vector DB
    dim = len(embeddings[0])
    store = VectorStore(dim)
    store.add(embeddings, texts)

    return store, embedder