# app/main.py
"""
Pharma-Flow — Application Entry Point

Initializes the multi-agent pipeline and runs the two clinical demo
scenarios.

Fix m-4: replaced bare print() calls with structured logging where
possible, while keeping the user-facing demo output readable on stdout.
"""
import sys

if sys.platform.startswith("win"):
    sys.stdout.reconfigure(encoding="utf-8")

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# ── Environment loading ───────────────────────────────────────────────────────
base_dir = Path(__file__).resolve().parent.parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path if env_path.exists() else base_dir / ".env.txt")

# Ensure the project root is in sys.path so imports work regardless of how the script is run
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))

# ── Application imports (after dotenv so env vars are available) ──────────────
from app.config.settings import settings  # noqa: E402
from services.query_service import QueryService  # noqa: E402

logging.basicConfig(
    level=logging.WARNING,          # suppress verbose INFO from 3rd-party libs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_log = logging.getLogger("pharma_flow.main")


def _print_banner(text: str) -> None:
    print(f"\n{'─' * 60}\n  {text}\n{'─' * 60}")


# ── Demo scenarios ────────────────────────────────────────────────────────────

SCENARIO_1 = {
    "sku": "PARA-500",
    "sku_name": "Paracetamol",
    "location_type": "hospital",
    "stock": 0,
    "on_order": 0,
    "forecast_demand": 500,
    "expiry_days": 60,
    "available_stock": 0,
    "confidence_low": 90,
    "confidence_high": 95,
}

SCENARIO_2 = {
    "sku": "ASP-100",
    "sku_name": "Aspirin",
    "location_type": "warehouse",
    "stock": 10,
    "on_order": 0,
    "forecast_demand": 100,
    "expiry_days": 100,
    "available_stock": 10,
    "confidence_low": 1,
    "confidence_high": 99,
}


if __name__ == "__main__":
    # Validate critical configuration at startup.
    if not settings.groq_api_key:
        _log.critical("GROQ_API_KEY is not set.")
        print("\n❌ ERROR: GROQ_API_KEY not found in your .env file!")
        print("💡 Copy .env.example → .env and add your Groq key.")
        sys.exit(1)

    _print_banner("PHARMA-FLOW  |  Multi-Agent Supply Chain Intelligence")

    print("\n⏭️  STEP 1: PubMed ingestion skipped (Development Mode)")
    print("           Enable by uncommenting IngestionService in this file.\n")

    print("🤖 STEP 2: Initializing Pharma-Flow Multi-Agent System...")
    service = QueryService(api_key=settings.groq_api_key)

    _print_banner("SCENARIO 1 — Clinical Shortage (Paracetamol, Hospital)")
    service.execute_agent_decision(SCENARIO_1)

    _print_banner("SCENARIO 2 — Data Uncertainty (Aspirin, Warehouse)")
    service.execute_agent_decision(SCENARIO_2)

    print("\n✅  SPRINT 2 DEMO COMPLETED SUCCESSFULLY ✅\n")