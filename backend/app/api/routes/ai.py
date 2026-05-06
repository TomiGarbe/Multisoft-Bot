import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_tenant
from app.api.dependencies.permissions import require_permission
from app.db.session import get_db
from app.schemas.ai import AITestRequest, AITestResponse
from app.services.ai.orchestration_service import AIOrchestrationService

router = APIRouter(tags=["AI"])


@router.post("/test", response_model=AITestResponse)
async def test_ai(
    body: AITestRequest,
    db: Session = Depends(get_db),
    current_tenant_id: uuid.UUID = Depends(get_current_tenant),
    _: None = Depends(require_permission("ai.test")),
):
    service = AIOrchestrationService(db)
    try:
        return await service.run_test(request=body, tenant_id=current_tenant_id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
