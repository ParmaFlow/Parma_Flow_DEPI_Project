# services/ingestion_service.py
"""
Ingestion Service — fetches PubMed abstracts and writes the RAG corpus.

Fixes applied:
    C-2: Hardcoded personal email removed. Email sourced from ENTREZ_EMAIL
         env var via settings.  PubMedAPI validates it at construction.
    M-6: API response is validated before writing to disk.  Empty or
         suspiciously short responses (NCBI error pages, rate-limit HTML)
         are rejected with a clear exception rather than silently poisoning
         the RAG corpus.
"""
import logging
import os
from pathlib import Path

from app.config.settings import settings
from data_sources.pubmed_api import PubMedAPI

logger = logging.getLogger(__name__)

# Minimum acceptable byte length for a PubMed API response.
# Responses shorter than this are almost certainly error pages or empty.
_MIN_RESPONSE_BYTES = 200


class IngestionService:
    """
    Fetches PubMed paper abstracts and stores them as the local RAG corpus.
    """

    def __init__(self) -> None:
        # C-2 fix: email sourced from env var, never hardcoded.
        # PubMedAPI.__init__ will raise ValueError if ENTREZ_EMAIL is empty.
        self.api = PubMedAPI(
            email=settings.entrez_email,
            api_key=settings.entrez_api_key or None,
        )
        self.file_path = Path(settings.pubmed_data_path)

    def ingest_pubmed(self, query: str) -> str:
        """
        Fetch abstracts for `query` from PubMed and write them to the
        local RAG corpus file.

        Inputs:
            query: PubMed search string.
        Outputs:
            str: the raw text written to disk.
        Raises:
            ValueError: if the API response is empty or suspiciously short
                        (M-6: prevents corpus poisoning).
            OSError: if the corpus file cannot be written.
        """
        logger.info("Fetching PubMed data for query: %r", query)
        raw_data = self.api.fetch_papers(query, max_results=settings.pubmed_max_results)

        # M-6 fix: validate before writing.
        if not raw_data or len(raw_data.strip()) < _MIN_RESPONSE_BYTES:
            raise ValueError(
                f"PubMed returned an empty or invalid response for query {query!r}. "
                f"Response length: {len(raw_data or '')} bytes "
                f"(minimum expected: {_MIN_RESPONSE_BYTES} bytes). "
                "This may indicate a rate-limit error, network issue, or "
                "no results for the given query.  Check ENTREZ_EMAIL and "
                "network connectivity."
            )

        # Ensure the output directory exists.
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        self.file_path.write_text(raw_data, encoding="utf-8")
        logger.info("PubMed corpus saved to %s (%d bytes)", self.file_path, len(raw_data))
        return raw_data