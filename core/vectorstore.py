# core/vectorstore.py
import faiss
import numpy as np


class VectorStore:
    """
    Thin FAISS wrapper for embedding-based nearest-neighbour retrieval.

    Thread-safety: FAISS IndexFlat is NOT thread-safe for concurrent writes.
    For the current single-threaded ingestion + read-only query pattern this
    is fine; add a lock if concurrent ingestion is introduced.
    """

    def __init__(self, dim: int) -> None:
        self.index = faiss.IndexFlatL2(dim)
        self.texts: list = []

    def add(self, embeddings, texts: list) -> None:
        """
        Add a batch of embeddings and their corresponding text chunks.

        Inputs:
            embeddings: array-like of shape (N, dim).
            texts: list of N text strings, parallel to embeddings.
        """
        self.index.add(np.array(embeddings, dtype=np.float32))
        self.texts.extend(texts)

    def search(self, query_embedding, k: int = 3) -> list:
        """
        Return up to k nearest text chunks for a query embedding.

        Inputs:
            query_embedding: 1-D array of shape (dim,).
            k: number of neighbours to retrieve. Clamped to the number of
               stored documents so callers don't have to know the corpus size.
        Outputs:
            list[str]: matching text chunks, ordered by ascending L2 distance.
                       May be shorter than k if fewer documents are indexed.

        Fix M-5: FAISS returns index -1 for unfilled slots when the index
        contains fewer than k documents.  Previously self.texts[-1] would
        silently return the last document (wrong data, no error).  Now -1
        sentinels are explicitly filtered out.
        """
        if not self.texts:
            return []

        # Clamp k so FAISS never returns more slots than we have documents.
        effective_k = min(k, len(self.texts))

        _distances, indices = self.index.search(
            np.array([query_embedding], dtype=np.float32), effective_k
        )

        results = []
        for idx in indices[0]:
            if idx == -1:
                # FAISS sentinel: fewer real neighbours than requested k.
                continue
            if 0 <= idx < len(self.texts):
                results.append(self.texts[idx])

        return results