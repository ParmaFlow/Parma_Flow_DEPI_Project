from fastapi import APIRouter, Depends

from backend.api.schemas import InventoryCaseRequest, UserProfile, WorkflowDashboardResponse
from backend.api.security import get_current_user
from backend.api.services import run_workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("/analyze", response_model=WorkflowDashboardResponse)
def analyze(
    request: InventoryCaseRequest,
    user: UserProfile = Depends(get_current_user),
) -> WorkflowDashboardResponse:
    return run_workflow(request, user.role)

