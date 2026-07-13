from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    PHARMACIST = "pharmacist"
    EXECUTIVE = "executive"


class LoginRequest(BaseModel):
    username: str
    password: str


class UserProfile(BaseModel):
    username: str
    display_name: str
    role: UserRole


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class InventoryCaseRequest(BaseModel):
    sku: Optional[str] = None
    sku_name: str
    location_id: Optional[str] = None
    location_type: str = "warehouse"
    available_stock: int = Field(ge=0)
    forecast_demand: int
    lead_time: int = Field(default=0, ge=0)
    expiry_days: Optional[int] = None
    confidence_low: Optional[float] = None
    confidence_high: Optional[float] = None
    stock: Optional[int] = None
    on_order: int = Field(default=0, ge=0)
    safety_stock: Optional[int] = None
    avg_daily_demand: Optional[float] = None
    max_daily_demand: Optional[float] = None
    avg_lead_time: Optional[float] = None
    max_lead_time: Optional[float] = None
    drug_category: Optional[str] = None


class RAGContextRequest(BaseModel):
    query: str
    k: int = Field(default=2, ge=1, le=10)


class RAGChatRequest(BaseModel):
    message: str
    k: int = Field(default=3, ge=1, le=10)
    inventory_context: Optional[str] = None


class RAGChatResponse(BaseModel):
    response: str
    context_used: bool


class WorkflowExecutionMeta(BaseModel):
    execution_id: str
    status: str
    current_step: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    failed_step: Optional[str] = None
    error_message: Optional[str] = None
    step_durations: Dict[str, float] = Field(default_factory=dict)


class ActionAlert(BaseModel):
    severity: str
    title: str
    message: str
    owner: str


class WorkflowDashboardResponse(BaseModel):
    role: UserRole
    execution: WorkflowExecutionMeta
    input: Optional[Dict[str, Any]] = None
    operational: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    audit: Optional[Dict[str, Any]] = None
    report: Optional[Dict[str, Any]] = None
    actionable_alerts: List[ActionAlert] = Field(default_factory=list)
    kpis: Dict[str, Any] = Field(default_factory=dict)
    traces: List[Dict[str, Any]] = Field(default_factory=list)
    system_logs: List[str] = Field(default_factory=list)
    compliance: Dict[str, Any] = Field(default_factory=dict)


class InventoryItem(BaseModel):
    sku_id: Optional[str] = None
    generic_name: Optional[str] = None
    stock: Optional[int] = None
    forecast_demand: Optional[int] = None
    expiry_days: Optional[int] = None
    raw: Dict[str, Any]


class InventorySummary(BaseModel):
    sku_count: int
    total_stock: int
    total_forecast_demand: int
    shortage_candidates: int



