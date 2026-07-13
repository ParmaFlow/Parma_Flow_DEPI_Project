from fastapi import APIRouter, Depends, HTTPException

from backend.api.schemas import InventoryCaseRequest, UserProfile, WorkflowDashboardResponse
from backend.api.security import get_current_user
from backend.api.services import run_workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/analyze", response_model=WorkflowDashboardResponse)
def analyze(
    request: InventoryCaseRequest,
    user: UserProfile = Depends(get_current_user),
) -> WorkflowDashboardResponse:
    try:
        return run_workflow(request, user.role)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - API boundary
        raise HTTPException(
            status_code=500,
            detail=f"Workflow analysis failed: {exc}",
        ) from exc
