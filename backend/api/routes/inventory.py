from typing import Dict, List

from fastapi import APIRouter, Depends

from backend.api.schemas import InventoryItem, InventorySummary, UserProfile
from backend.api.security import get_current_user
from backend.api.services import list_inventory_items, summarize_eda_dataset, summarize_inventory

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/items", response_model=List[InventoryItem])
def items(_: UserProfile = Depends(get_current_user)) -> List[InventoryItem]:
    return list_inventory_items()


@router.get("/summary", response_model=InventorySummary)
def summary(_: UserProfile = Depends(get_current_user)) -> InventorySummary:
    return summarize_inventory()


@router.get("/eda-summary", response_model=Dict[str, object])
def eda_summary(_: UserProfile = Depends(get_current_user)) -> Dict[str, object]:
    return summarize_eda_dataset()

