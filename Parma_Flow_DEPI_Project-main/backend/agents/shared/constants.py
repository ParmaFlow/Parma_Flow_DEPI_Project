# backend/agents/shared/constants.py
"""
Centralized business constants shared across agents.
"""
from enum import Enum

# --- Ops Agent constants ---------------------------------------------------

REORDER_ROUNDING = 10
DEFAULT_WAREHOUSE_ASSIGNEE = "Warehouse Ops"
DEFAULT_HOSPITAL_ASSIGNEE = "Pharmacy Manager"

# Heuristics used when historical demand/lead-time distributions are
# unavailable. These provide a deterministic, documented fallback instead
# of guessing silently.
SAFETY_STOCK_MAX_DEMAND_MULTIPLIER = 1.5   # used to estimate max daily demand
SAFETY_STOCK_MAX_LEAD_TIME_MULTIPLIER = 1.3  # used to estimate max lead time
SAFETY_STOCK_MINIMUM = 0

# Inventory status thresholds, expressed as a ratio of available_stock to
# reorder_point (ROP). available_stock <= 0 is always OUT_OF_STOCK.
CRITICAL_STOCK_RATIO = 0.5   # stock <= 50% of ROP => CRITICAL
LOW_STOCK_RATIO = 1.0        # stock <= 100% of ROP (but > 50%) => LOW

# --- Risk Agent constants ---------------------------------------------------

# Risk score bands (0-100 scale), inclusive upper bounds.
LOW_RISK_THRESHOLD = 25
MEDIUM_RISK_THRESHOLD = 50
HIGH_RISK_THRESHOLD = 75
# Anything above HIGH_RISK_THRESHOLD is CRITICAL.

# Score at/above which autonomous execution should be downgraded to
# HUMAN_REVIEW rather than proceeding automatically.
HUMAN_REVIEW_RISK_THRESHOLD = 70

EXPIRY_WARNING_DAYS = 30
LONG_LEAD_TIME_DAYS = 21

# Contribution weights (points out of 100) for each deterministic risk
# factor. Sum of all weights should not exceed 100.
CONFIDENCE_WIDTH_WEIGHT = 20
LOW_STOCK_WEIGHT = 15
SHORTAGE_RISK_WEIGHT = 25
EXPIRY_RISK_WEIGHT = 20
CRITICAL_DRUG_WEIGHT = 10
LONG_LEAD_TIME_WEIGHT = 10

# A confidence interval is "very wide" if its width exceeds this fraction
# of forecast_demand.
CONFIDENCE_WIDTH_RATIO_THRESHOLD = 0.30

# Stock is considered "low" if available_stock is below this fraction of
# forecast_demand.
LOW_STOCK_RATIO_THRESHOLD = 0.20

CRITICAL_DRUG_CATEGORIES = {
    "insulin",
    "chemotherapy",
    "anesthesia",
    "anticoagulant",
    "vaccine",
    "emergency",
}

MIN_RISK_SCORE = 0
MAX_RISK_SCORE = 100

# --- Auditor Agent constants -------------------------------------------------

VALID_ACTIONS = {"REORDER", "MONITOR"}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_CRITICALITY_LEVELS = {"CRITICAL", "STANDARD"}

MAX_BLOCKING_ERRORS = 0
MAX_ALLOWED_WARNINGS = 5

# A product is considered expired (not just near-expiry) at or below this
# many days remaining.
EXPIRED_PRODUCT_DAYS = 0
ABSURD_FORECAST_THRESHOLD = 1_000_000


class RuleSeverity(str, Enum):
    """Severity classification for a single Auditor rule outcome."""

    WARNING = "WARNING"
    ERROR = "ERROR"
    BLOCKER = "BLOCKER"


# --- Shared Enums ------------------------------------------------------------


class ExecutionStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ActionType(str, Enum):
    REORDER = "REORDER"
    MONITOR = "MONITOR"
    REDISTRIBUTE = "REDISTRIBUTE"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    AUDIT = "AUDIT"


class InventoryStatus(str, Enum):
    NORMAL = "NORMAL"
    LOW = "LOW"
    CRITICAL = "CRITICAL"
    OUT_OF_STOCK = "OUT_OF_STOCK"