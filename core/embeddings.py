# core/embeddings.py
"""
Embedding model wrapper for the RAG pipeline.

Wraps sentence-transformers so the rest of the codebase never imports
sentence_transformers directly — making it trivial to swap models later.
"""
from app.config.settings import settings


class EmbeddingModel:
    """
    Thin wrapper around a SentenceTransformer embedding model.

    The model name is read from settings.embedding_model (env var
    EMBEDDING_MODEL), defaulting to "all-MiniLM-L6-v2".
    """

    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer  # lazy import

        resolved = model_name or settings.embedding_model
        self.model = SentenceTransformer(resolved)

    def embed(self, texts: list[str]) -> list:
        """
        Encode a list of text strings into embedding vectors.

        Inputs:
            texts: list of strings to embed. Fix m-2: parameter was named
                   `Texts` (capital T), violating PEP 8.
        Outputs:
            numpy ndarray of shape (len(texts), embedding_dim).
        """
        return self.model.encode(texts)