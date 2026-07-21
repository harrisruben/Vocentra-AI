from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import User, Organization, AuditLog
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.core.logger import logger
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/dashboard/settings", tags=["Settings"])

class SettingsUpdatePayload(BaseModel):
    twilio_sid: Optional[str] = None
    twilio_token: Optional[str] = None
    vapi_assistant_id: Optional[str] = None
    n8n_webhook_url: Optional[str] = None
    call_delay: Optional[int] = None

@router.get("", response_model=StandardResponse[dict])
async def get_workspace_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    org_id = current_user.organization_id
    org_res = await db.execute(select(Organization).filter(Organization.id == org_id))
    org = org_res.scalar()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return StandardResponse(
        success=True,
        message="Workspace settings loaded successfully",
        data={
            "twilio_sid": org.twilio_sid or "",
            "twilio_token": org.twilio_token or "",
            "vapi_assistant_id": org.vapi_assistant_id or "",
            "n8n_webhook_url": org.n8n_webhook_url or "",
            "call_delay": org.call_delay if org.call_delay is not None else 30
        }
    )

@router.put("", response_model=StandardResponse[dict])
async def update_workspace_settings(
    payload: SettingsUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role.lower() not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only workspace admins can modify settings.")
        
    org_id = current_user.organization_id
    org_res = await db.execute(select(Organization).filter(Organization.id == org_id))
    org = org_res.scalar()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    if payload.twilio_sid is not None:
        org.twilio_sid = payload.twilio_sid
    if payload.twilio_token is not None:
        org.twilio_token = payload.twilio_token
    if payload.vapi_assistant_id is not None:
        org.vapi_assistant_id = payload.vapi_assistant_id
    if payload.n8n_webhook_url is not None:
        org.n8n_webhook_url = payload.n8n_webhook_url
    if payload.call_delay is not None:
        org.call_delay = payload.call_delay
    
    # Log audit entry
    log = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action="settings_modified",
        description="Modified Twilio/Vapi API workspace credentials and integration webhook paths",
        ip_address="127.0.0.1"
    )
    db.add(log)
    await db.commit()
    
    return StandardResponse(
        success=True,
        message="Workspace settings updated successfully.",
        data={
            "twilio_sid": org.twilio_sid or "",
            "twilio_token": org.twilio_token or "",
            "vapi_assistant_id": org.vapi_assistant_id or "",
            "n8n_webhook_url": org.n8n_webhook_url or "",
            "call_delay": org.call_delay if org.call_delay is not None else 30
        }
    )
