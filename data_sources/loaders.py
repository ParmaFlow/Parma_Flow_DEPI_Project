# data_sources/loaders.py
"""
Document loaders for the Pharma-Flow RAG pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """
    Represents a single text document loaded for RAG indexing.

    Attributes:
        content:  The raw text body of the document.
        metadata: Arbitrary key-value metadata (source, id, etc.).

    Fix C-4: `load_pubmed_text` was defined as a plain method but used as
    a static call (Document.load_pubmed_text(path)).  In Python 3 this
    accidentally works at the class level — but is a contract violation and
    silently corrupts on any instance-level call.  Now properly declared
    with @staticmethod.

    Fix m-3: converted to @dataclass for __repr__, __eq__, and type safety.
    """

    content: str
    metadata: dict = field(default_factory=dict)

    @staticmethod
    def load_pubmed_text(file_path: str | Path) -> list[Document]:
        """
        Load a plain-text PubMed corpus file and split it into Documents.

        Paragraphs are separated by blank lines.  Paragraphs shorter than
        50 characters after stripping are discarded (header/metadata noise).

        Inputs:
            file_path: path to the corpus file (e.g. data/raw/pubmed.txt).
        Outputs:
            list[Document]: one Document per paragraph, with an "id"
                            metadata field for traceability.
        Raises:
            FileNotFoundError: if file_path does not exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(
                f"PubMed corpus not found at '{path}'. "
                "Run IngestionService.ingest_pubmed() to populate it first."
            )

        text = path.read_text(encoding="utf-8")
        paragraphs = text.split("\n\n")

        documents: list[Document] = []
        for i, para in enumerate(paragraphs):
            stripped = para.strip()
            if len(stripped) > 50:
                documents.append(Document(content=stripped, metadata={"id": i}))

        return documents