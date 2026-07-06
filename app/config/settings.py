# app/config/settings.py
"""
Centralized application configuration for Pharma-Flow.

All runtime tunables are sourced from environment variables with safe,
documented defaults. No hardcoded values should exist anywhere else in
the codebase — import `settings` from this module instead.

Usage:
    from app.config.settings import settings
    model = settings.llm_model
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

# Absolute path to the project root (three levels up from this file:
# settings.py → config/ → app/ → project root)
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def _env_str(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    """
    Runtime configuration for all Pharma-Flow subsystems.

    Every field maps 1-to-1 to an environment variable.  The name of the
    env var is the field name in UPPER_SNAKE_CASE.  Defaults reproduce the
    original hardcoded behavior exactly so existing setups require no .env
    changes unless they want to override.
    """

    # ── LLM / Groq ───────────────────────────────────────────────────────────
    groq_api_key: str = field(
        default_factory=lambda: _env_str("GROQ_API_KEY", "")
    )
    llm_model: str = field(
        default_factory=lambda: _env_str("LLM_MODEL", "llama-3.1-8b-instant")
    )
    llm_base_url: str = field(
        default_factory=lambda: _env_str(
            "LLM_BASE_URL", "https://api.groq.com/openai/v1"
        )
    )
    llm_timeout_seconds: float = field(
        default_factory=lambda: _env_float("LLM_TIMEOUT_SECONDS", 30.0)
    )
    llm_max_retries: int = field(
        default_factory=lambda: _env_int("LLM_MAX_RETRIES", 3)
    )
    llm_temperature: float = field(
        default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.2)
    )
    llm_max_tokens: int = field(
        default_factory=lambda: _env_int("LLM_MAX_TOKENS", 800)
    )

    # ── Data Ingestion / NCBI Entrez ─────────────────────────────────────────
    entrez_email: str = field(
        default_factory=lambda: _env_str("ENTREZ_EMAIL", "")
    )
    entrez_api_key: str = field(
        default_factory=lambda: _env_str("ENTREZ_API_KEY", "")
    )
    pubmed_data_path: str = field(
        default_factory=lambda: _env_str(
            "PUBMED_DATA_PATH",
            str(_ROOT_DIR / "data" / "raw" / "pubmed.txt"),
        )
    )
    pubmed_max_results: int = field(
        default_factory=lambda: _env_int("PUBMED_MAX_RESULTS", 10)
    )

    # ── RAG / Embeddings ─────────────────────────────────────────────────────
    embedding_model: str = field(
        default_factory=lambda: _env_str("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    rag_chunk_size: int = field(
        default_factory=lambda: _env_int("RAG_CHUNK_SIZE", 300)
    )
    rag_chunk_overlap: int = field(
        default_factory=lambda: _env_int("RAG_CHUNK_OVERLAP", 50)
    )
    rag_retrieval_k: int = field(
        default_factory=lambda: _env_int("RAG_RETRIEVAL_K", 3)
    )

    def validate(self) -> None:
        """
        Raise ValueError for any fatal misconfiguration that would cause
        a runtime crash later.  Call this at application startup.
        """
        if not self.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )
        if not self.entrez_email:
            raise ValueError(
                "ENTREZ_EMAIL is not set. NCBI TOS require an institutional "
                "email for Entrez API access. Add it to your .env file."
            )
        if self.rag_chunk_overlap >= self.rag_chunk_size:
            raise ValueError(
                f"RAG_CHUNK_OVERLAP ({self.rag_chunk_overlap}) must be less "
                f"than RAG_CHUNK_SIZE ({self.rag_chunk_size})."
            )


# Module-level singleton — import this everywhere.
settings = Settings()
