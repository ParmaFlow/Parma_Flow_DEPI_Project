# rag/chunking.py
"""
Text chunking utilities for the RAG pipeline.

Splits raw document text into overlapping chunks suitable for embedding
and nearest-neighbour retrieval.
"""
from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping fixed-size character chunks.

    Inputs:
        text: the raw string to chunk. Empty strings return [].
        chunk_size: character length of each chunk (must be > overlap).
        overlap: number of characters shared between consecutive chunks.
    Outputs:
        list[str]: ordered list of text chunks.
    Raises:
        ValueError: if overlap >= chunk_size (would cause infinite loop).

    Fix M-7: previous implementation had no guard — passing overlap >= chunk_size
    caused `start` to never advance, hanging the process indefinitely.
    """
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError(
            f"overlap ({overlap}) must be strictly less than "
            f"chunk_size ({chunk_size}) to avoid an infinite loop."
        )

    chunks: list[str] = []
    stride = chunk_size - overlap  # guaranteed > 0 by the guard above
    start = 0

    while start < len(text):
        chunks.append(text[start : start + chunk_size])
        start += stride

    return chunks


def chunk_documents(documents: list, chunk_size: int = 300, overlap: int = 50) -> list[dict]:
    """
    Chunk a list of Document objects into a flat list of chunk dicts.

    Inputs:
        documents: list of objects with `.content` (str) and `.metadata` (dict).
        chunk_size: forwarded to chunk_text().
        overlap: forwarded to chunk_text().
    Outputs:
        list[dict]: each item has keys "content" (str) and "metadata" (dict).
                    Empty documents (after chunking) are silently skipped.
    """
    all_chunks: list[dict] = []

    for doc in documents:
        chunks = chunk_text(doc.content, chunk_size=chunk_size, overlap=overlap)
        for chunk in chunks:
            if chunk.strip():  # skip whitespace-only chunks
                all_chunks.append({"content": chunk, "metadata": doc.metadata})

    return all_chunks
