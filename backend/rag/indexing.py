# rag/indexing.py
"""
RAG index builder.

Fixes applied:
    C-3: Added file existence check and empty-corpus guard with actionable
         error messages, preventing cryptic FileNotFoundError or IndexError
         crashes that occurred when data/raw/pubmed.txt was absent (it is
         in .gitignore, so absent on every fresh clone).
"""
import logging
import os
from pathlib import Path

from backend.data_sources.loaders import Document
from backend.rag.chunking import chunk_documents
from backend.core.embeddings import EmbeddingModel
from backend.core.vectorstore import VectorStore
from backend.config.settings import settings

logger = logging.getLogger(__name__)


def build_index(file_path: str | Path | None = None) -> tuple[VectorStore, EmbeddingModel]:
    """
    Build a FAISS vector index from the local PubMed corpus.

    Inputs:
        file_path: path to the plain-text corpus file.  Defaults to
                   settings.pubmed_data_path (PUBMED_DATA_PATH env var).
    Outputs:
        tuple[VectorStore, EmbeddingModel]: ready for use by the retriever.
    Raises:
        FileNotFoundError: if the corpus file does not exist.
        ValueError: if the corpus yields zero indexable documents or chunks.
    """
    resolved = Path(file_path or settings.pubmed_data_path)

    # C-3 fix â€” guard #1: file existence check with actionable message.
    if not resolved.exists():
        raise FileNotFoundError(
            f"RAG corpus not found at '{resolved}'. "
            "Run IngestionService.ingest_pubmed() first to fetch and store "
            "PubMed abstracts, or copy a pre-built pubmed.txt to that path."
        )

    logger.info("Loading RAG corpus from %s", resolved)
    documents = Document.load_pubmed_text(resolved)

    # C-3 fix â€” guard #2: empty corpus produces a useless index.
    if not documents:
        raise ValueError(
            f"RAG corpus at '{resolved}' loaded 0 documents. "
            "The file may be empty or contain only short paragraphs (<50 chars). "
            "Re-run IngestionService.ingest_pubmed() with a valid query."
        )

    chunks = chunk_documents(
        documents,
        chunk_size=settings.rag_chunk_size,
        overlap=settings.rag_chunk_overlap,
    )

    # Guard #3: chunking may return nothing if all content is whitespace.
    if not chunks:
        raise ValueError(
            f"RAG corpus at '{resolved}' produced 0 text chunks after splitting. "
            "Check RAG_CHUNK_SIZE and RAG_CHUNK_OVERLAP settings."
        )

    texts = [c["content"] for c in chunks]

    embedder = EmbeddingModel()
    embeddings = embedder.embed(texts)

    # Guard #4: embedding model returned empty array.
    if len(embeddings) == 0:
        raise ValueError("Embedding model returned 0 vectors. Check EMBEDDING_MODEL setting.")

    dim = len(embeddings[0])
    store = VectorStore(dim)
    store.add(embeddings, texts)

    logger.info(
        "RAG index built: %d documents â†’ %d chunks â†’ %d-dim vectors",
        len(documents), len(chunks), dim,
    )
    return store, embedder
