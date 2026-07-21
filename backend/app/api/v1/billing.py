from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import User, Organization, AuditLog
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.core.logger import logger
import datetime

router = APIRouter(prefix="/dashboard/billing", tags=["Billing"])

@router.get("", response_model=StandardResponse[dict])
async def get_billing_status(
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
        message="Billing details loaded successfully",
        data={
            "billing_tier": org.billing_tier,
            "usage_limit": org.usage_limit,
            "usage_count": org.usage_count,
            "created_at": org.created_at.isoformat()
        }
    )

@router.put("/upgrade", response_model=StandardResponse[dict])
async def upgrade_billing_tier(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role.lower() not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only workspace admins can modify subscriptions.")
        
    tier = payload.get("tier", "free").lower()
    if tier not in ["free", "growth", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid billing tier.")
        
    org_id = current_user.organization_id
    org_res = await db.execute(select(Organization).filter(Organization.id == org_id))
    org = org_res.scalar()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    old_tier = org.billing_tier
    org.billing_tier = tier
    
    if tier == "free":
        org.usage_limit = 100
    elif tier == "growth":
        org.usage_limit = 1000
    elif tier == "enterprise":
        org.usage_limit = 1000000
        
    # Log audit entry
    log = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action="settings_modified",
        description=f"Upgraded subscription plan from '{old_tier}' to '{tier}' (quota limit adjusted to {org.usage_limit})",
        ip_address="127.0.0.1"
    )
    db.add(log)
    await db.commit()
    
    return StandardResponse(
        success=True,
        message=f"Plan upgraded to {tier} successfully.",
        data={
            "billing_tier": org.billing_tier,
            "usage_limit": org.usage_limit,
            "usage_count": org.usage_count
        }
    )
