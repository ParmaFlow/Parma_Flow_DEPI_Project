# data_sources/pubmed_api.py
"""
PubMed / NCBI Entrez API client.

Security note (C-1 fix): the original file contained a global SSL monkey-
patch that disabled certificate verification for the entire Python process:

    ssl._create_default_https_context = ssl._create_unverified_context  # REMOVED

This has been removed.  Modern Biopython (>=1.83) uses Python's default SSL
context, which correctly loads the certifi CA bundle when certifi is installed
(see requirements.txt).  No explicit ssl_context wiring is needed.
"""
import time

from Bio import Entrez


class PubMedAPI:
    """
    Thin wrapper around Biopython's Entrez utilities.

    Args:
        email:   Institutional email address (required by NCBI TOS for
                 caller identification).  Loaded from ENTREZ_EMAIL env var
                 via IngestionService — never hardcoded.
        api_key: Optional NCBI API key.  Raises rate limits from 3 to 10
                 requests/second when provided.
    """

    def __init__(self, email: str, api_key: str | None = None) -> None:
        # C-2 fix: never accept an empty email — callers must supply a real
        # institutional address via ENTREZ_EMAIL env var.
        if not email or not email.strip():
            raise ValueError(
                "PubMedAPI requires a non-empty institutional email address. "
                "Set the ENTREZ_EMAIL environment variable in your .env file. "
                "NCBI Terms of Service require caller identification for all "
                "Entrez API requests."
            )
        Entrez.email = email.strip()
        if api_key:
            Entrez.api_key = api_key.strip()

    def search(self, query: str, max_results: int = 10) -> list[str]:
        """
        Search PubMed for article IDs matching a query.

        Inputs:
            query: PubMed search string.
            max_results: maximum number of article IDs to return.
        Outputs:
            list[str]: PubMed IDs (PMIDs).
        """
        with Entrez.esearch(db="pubmed", term=query, retmax=max_results) as handle:
            record = Entrez.read(handle)
        return record["IdList"]

    def fetch_details(self, id_list: list[str]) -> str:
        """
        Fetch abstracts for a list of PubMed IDs.

        Inputs:
            id_list: list of PMIDs returned by search().
        Outputs:
            str: concatenated plain-text abstracts.
        """
        if not id_list:
            return ""
        ids = ",".join(id_list)
        with Entrez.efetch(db="pubmed", id=ids, rettype="abstract", retmode="text") as handle:
            return handle.read()

    def fetch_papers(self, query: str, max_results: int = 10) -> str:
        """
        Search and fetch abstracts in one call.

        Inputs:
            query: PubMed search string.
            max_results: maximum articles.
        Outputs:
            str: plain-text abstracts.
        """
        ids = self.search(query, max_results)
        if not ids:
            return ""
        time.sleep(1)  # NCBI rate-limit courtesy delay
        return self.fetch_details(ids)