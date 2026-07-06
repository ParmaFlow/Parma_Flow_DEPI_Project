# rag/pipline.py
"""
DEPRECATED — this module contains a typo in its filename.

Please import from `rag.pipeline` (correctly spelled) instead:

    from rag.pipeline import RAGPipeline   # ✅ correct
    from rag.pipline import RAGPipeline    # ❌ deprecated

This file is kept temporarily to avoid breaking any cached imports in
__pycache__.  It will be removed in the next sprint cleanup.
"""
import warnings

warnings.warn(
    "rag.pipline is deprecated and will be removed. "
    "Use 'from rag.pipeline import RAGPipeline' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from rag.pipeline import RAGPipeline  # noqa: F401, E402 — re-export for backward compat