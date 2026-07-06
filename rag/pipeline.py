# rag/pipeline.py
"""
RAG Pipeline — canonical module (replaces the misspelled `pipline.py`).

Fix m-1: renamed from `pipline.py` to `pipeline.py`.
Fix M-2: replaced the `# placeholder LLM` stub with a proper docstring
         explaining the integration contract and a clean context-retrieval
         implementation. Full LLM synthesis is intentionally deferred to
         the agent layer (OpsAgent receives retrieved context) rather than
         duplicating LLM logic here.
"""
from __future__ import annotations

import logging

from rag.indexing import build_index
from rag.retriever import retrieve

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end retrieval-augmented generation pipeline.

    Responsibilities:
        1. Build (or receive) a FAISS vector index from a corpus file.
        2. Accept free-text queries and return the most relevant text chunks.

    The pipeline deliberately does NOT call the LLM itself.  Generating
    a synthesized answer is the responsibility of the agent that consumes
    retrieved context (e.g. OpsAgent), keeping LLM invocation in one place
    (core/llm.py) and making the RAG layer independently testable.

    Usage:
        rag = RAGPipeline(file_path="data/raw/pubmed.txt")
        context_chunks = rag.retrieve_context("Paracetamol shortage alternatives")
        # Pass context_chunks to an LLMModel.get_decision() call.
    """

    def __init__(self, file_path: str | None = None) -> None:
        """
        Build the index.  Raises FileNotFoundError / ValueError if the
        corpus file is missing or empty (see rag/indexing.py for details).

        Inputs:
            file_path: path to corpus.  None → reads from settings.
        """
        self.store, self.embedder = build_index(file_path)
        logger.info("RAGPipeline ready.")

    def retrieve_context(self, query: str, k: int | None = None) -> list[str]:
        """
        Retrieve the top-k most relevant text chunks for a query.

        Inputs:
            query: free-text search query.
            k: number of chunks to retrieve.  None → reads from settings.
        Outputs:
            list[str]: relevant text chunks, ordered by relevance (closest first).
                       Empty list if the index is empty or query is blank.
        """
        from app.config.settings import settings  # deferred to avoid circular import

        if not query or not query.strip():
            logger.warning("RAGPipeline.retrieve_context called with empty query.")
            return []

        effective_k = k if k is not None else settings.rag_retrieval_k
        chunks = retrieve(query, self.store, self.embedder, k=effective_k)
        logger.debug("RAG retrieved %d chunks for query %r", len(chunks), query)
        return chunks

    def get_context_text(self, query: str, k: int | None = None) -> str:
        """
        Convenience wrapper: retrieve context and join into a single string
        ready for injection into an LLM prompt.

        Inputs:
            query: free-text search query.
            k: number of chunks (None → settings default).
        Outputs:
            str: newline-separated context paragraphs, or empty string.
        """
        chunks = self.retrieve_context(query, k=k)
        return "\n\n".join(chunks)
