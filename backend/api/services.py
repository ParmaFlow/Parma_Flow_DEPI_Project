from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List

from app.config.settings import settings
from backend.api.schemas import (
    ActionAlert,
    InventoryCaseRequest,
    InventoryItem,
    InventorySummary,
    UserRole,
    WorkflowDashboardResponse,
    WorkflowExecutionMeta,
)
from backend.bootstrap import build_orchestrator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SPRINT_OUTPUT_PATH = PROJECT_ROOT / "data" / "sprint1_output.json"
FINAL_DATASET_PATH = PROJECT_ROOT / "data" / "final_dataset.csv"


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


@lru_cache(maxsize=1)
def load_inventory_data() -> List[Dict[str, Any]]:
    if not SPRINT_OUTPUT_PATH.exists():
        return []
    with SPRINT_OUTPUT_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def list_inventory_items() -> List[InventoryItem]:
    return [
        InventoryItem(
            sku_id=item.get("sku_id") or item.get("sku"),
            generic_name=item.get("generic_name") or item.get("sku_name"),
            stock=item.get("stock") or item.get("available_stock"),
            forecast_demand=item.get("forecast_demand"),
            expiry_days=item.get("expiry_days"),
            raw=item,
        )
        for item in load_inventory_data()
    ]


def summarize_inventory() -> InventorySummary:
    items = load_inventory_data()
    total_stock = sum(int(item.get("stock") or item.get("available_stock") or 0) for item in items)
    total_forecast = sum(int(item.get("forecast_demand") or 0) for item in items)
    shortage_candidates = sum(
        1
        for item in items
        if int(item.get("stock") or item.get("available_stock") or 0)
        < int(item.get("forecast_demand") or 0)
    )
    return InventorySummary(
        sku_count=len(items),
        total_stock=total_stock,
        total_forecast_demand=total_forecast,
        shortage_candidates=shortage_candidates,
    )


def summarize_eda_dataset() -> Dict[str, Any]:
    if not FINAL_DATASET_PATH.exists():
        return {"available": False}

    rows = 0
    net_sales = 0.0
    manufacturers = set()
    governorates = set()
    with FINAL_DATASET_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows += 1
            manufacturers.add(row.get("manufacturer", ""))
            governorates.add(row.get("governorate", ""))
            try:
                net_sales += float(row.get("actual_demand_units") or 0) * float(row.get("unit_price_egp") or 0)
            except ValueError:
                continue

    return {
        "available": True,
        "rows": rows,
        "manufacturer_count": len([value for value in manufacturers if value]),
        "governorate_count": len([value for value in governorates if value]),
        "net_sales_value_egp": round(net_sales, 2),
    }


def run_workflow(request: InventoryCaseRequest, role: UserRole) -> WorkflowDashboardResponse:
    api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY") or "local-mvp-placeholder"
    orchestrator = build_orchestrator(api_key)
    payload = request.dict(exclude_none=True)
    payload.setdefault("stock", request.available_stock)
    payload.setdefault("on_order", request.on_order)

    state = orchestrator.run(payload)
    return build_dashboard_response(state, role)


def build_dashboard_response(state: Any, role: UserRole) -> WorkflowDashboardResponse:
    operational = _jsonable(state.operational_result) if state.operational_result else None
    risk = _jsonable(state.risk_result) if state.risk_result else None
    audit = _jsonable(state.audit_result) if state.audit_result else None
    report = _jsonable(state.report_result) if state.report_result else None

    execution = WorkflowExecutionMeta(
        execution_id=state.execution_id,
        status=_jsonable(state.execution_status),
        current_step=state.current_step,
        start_time=_jsonable(state.start_time),
        end_time=_jsonable(state.end_time),
        failed_step=state.failed_step,
        error_message=state.error_message,
        step_durations=state.step_durations,
    )

    base = WorkflowDashboardResponse(
        role=role,
        execution=execution,
        input=_jsonable(state.original_input),
        actionable_alerts=_build_alerts(operational, risk, audit, report),
        kpis=_build_kpis(operational, risk, audit, report),
        compliance=_build_compliance(audit, report),
    )

    if role == UserRole.PHARMACIST:
        base.operational = operational
        base.risk = risk
        base.audit = _audit_summary(audit)
        base.report = _next_action_summary(report)
        return base

    if role == UserRole.EXECUTIVE:
        base.report = report
        base.audit = _audit_summary(audit)
        return base

    base.operational = operational
    base.risk = risk
    base.audit = audit
    base.report = report
    base.traces = _build_traces(state, operational, risk, audit, report)
    base.system_logs = _build_system_logs(state)
    return base


def _build_alerts(
    operational: Dict[str, Any] | None,
    risk: Dict[str, Any] | None,
    audit: Dict[str, Any] | None,
    report: Dict[str, Any] | None,
) -> List[ActionAlert]:
    alerts: List[ActionAlert] = []
    if operational and operational.get("inventory_gap", 0) > 0:
        alerts.append(
            ActionAlert(
                severity="critical",
                title="Inventory gap detected",
                message=(
                    f"Order {operational.get('recommended_qty', 0):,} units to cover "
                    f"{operational.get('inventory_gap', 0):,} units of shortage."
                ),
                owner=operational.get("assignee") or "Warehouse Ops",
            )
        )
    if risk and risk.get("human_review_recommended"):
        alerts.append(
            ActionAlert(
                severity="warning",
                title="Human review required",
                message=f"Risk score {risk.get('risk_score')}/100 requires manual review.",
                owner="Pharmacy Manager",
            )
        )
    if audit and not audit.get("approved", False):
        alerts.append(
            ActionAlert(
                severity="blocked",
                title="Execution blocked",
                message=f"Audit status {audit.get('audit_status')} prevents autonomous execution.",
                owner="Compliance Officer",
            )
        )
    if not alerts and report:
        alerts.append(
            ActionAlert(
                severity="normal",
                title="Monitor",
                message=report.get("reasoning") or "No immediate operational action is required.",
                owner="Inventory Control",
            )
        )
    return alerts


def _build_kpis(
    operational: Dict[str, Any] | None,
    risk: Dict[str, Any] | None,
    audit: Dict[str, Any] | None,
    report: Dict[str, Any] | None,
) -> Dict[str, Any]:
    return {
        "final_status": report.get("final_status") if report else None,
        "execution_allowed": report.get("execution_allowed") if report else False,
        "recommended_action": report.get("recommended_action") if report else None,
        "inventory_gap": operational.get("inventory_gap") if operational else 0,
        "recommended_qty": operational.get("recommended_qty") if operational else 0,
        "risk_score": risk.get("risk_score") if risk else None,
        "risk_level": risk.get("risk_level") if risk else None,
        "audit_status": audit.get("audit_status") if audit else None,
        "blocking_errors": audit.get("blocking_errors") if audit else 0,
        "warning_count": audit.get("warning_count") if audit else 0,
    }


def _build_compliance(audit: Dict[str, Any] | None, report: Dict[str, Any] | None) -> Dict[str, Any]:
    if not audit:
        return {"status": "UNAVAILABLE", "approved": False}
    return {
        "status": audit.get("audit_status"),
        "approved": audit.get("approved", False),
        "failed_rules": audit.get("failed_rules", []),
        "execution_allowed": report.get("execution_allowed") if report else False,
        "gxp_guardrail": "PASS" if audit.get("approved") else "BLOCKED",
    }


def _build_traces(
    state: Any,
    operational: Dict[str, Any] | None,
    risk: Dict[str, Any] | None,
    audit: Dict[str, Any] | None,
    report: Dict[str, Any] | None,
) -> List[Dict[str, Any]]:
    return [
        {"step": "ops", "duration_seconds": state.step_durations.get("ops"), "result": operational},
        {"step": "risk", "duration_seconds": state.step_durations.get("risk"), "result": risk},
        {"step": "audit", "duration_seconds": state.step_durations.get("audit"), "result": audit},
        {"step": "report", "duration_seconds": state.step_durations.get("report"), "result": report},
    ]


def _build_system_logs(state: Any) -> List[str]:
    logs = [
        f"{state.execution_id}: workflow started",
        f"{state.execution_id}: current_step={state.current_step}",
        f"{state.execution_id}: execution_status={_jsonable(state.execution_status)}",
    ]
    if state.failed_step:
        logs.append(f"{state.execution_id}: failed_step={state.failed_step}")
    if state.error_message:
        logs.append(f"{state.execution_id}: error={state.error_message}")
    return logs


def _audit_summary(audit: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if audit is None:
        return None
    return {
        "approved": audit.get("approved"),
        "audit_status": audit.get("audit_status"),
        "failed_rules": audit.get("failed_rules", []),
        "warning_count": audit.get("warning_count", 0),
        "blocking_errors": audit.get("blocking_errors", 0),
    }


def _next_action_summary(report: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if report is None:
        return None
    sections = report.get("report_sections") or {}
    return {
        "final_status": report.get("final_status"),
        "recommended_action": report.get("recommended_action"),
        "execution_allowed": report.get("execution_allowed"),
        "next_actions": sections.get("next_actions"),
    }

