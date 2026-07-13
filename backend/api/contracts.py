from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_NEXT_ACTION_ROLES = (
    "Procurement Officer",
    "Clinical Governance",
    "Supply Chain Lead",
)


def normalize_next_actions(value: Any) -> List[Dict[str, str]]:
    if isinstance(value, str):
        source_rows = [{"role": REQUIRED_NEXT_ACTION_ROLES[0], "action": value}]
    elif isinstance(value, list):
        source_rows = [row for row in value if isinstance(row, dict)]
    else:
        source_rows = []

    by_role = {
        str(row.get("role", "")).strip(): str(row.get("action", "")).strip()
        for row in source_rows
        if str(row.get("role", "")).strip() and str(row.get("action", "")).strip()
    }

    return [
        {
            "role": role,
            "action": by_role.get(role, "No prescriptive action generated for this role."),
        }
        for role in REQUIRED_NEXT_ACTION_ROLES
    ]



