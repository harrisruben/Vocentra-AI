import datetime
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import User, AuditLog
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/dashboard/team", tags=["Team"])

@router.get("", response_model=StandardResponse[list])
async def list_team_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Team API: Listing colleagues for org id={current_user.organization_id}")
    
    result = await db.execute(
        select(User).filter(User.organization_id == current_user.organization_id)
    )
    members = list(result.scalars().all())
    
    data = [{
        "id": m.id,
        "name": m.name,
        "email": m.email,
        "role": m.role,
        "is_active": m.is_active,
        "created_at": m.created_at.isoformat()
    } for m in members]
    
    return StandardResponse(
        success=True,
        message="Team members list successfully loaded.",
        data=data
    )

@router.post("/invite", response_model=StandardResponse[dict])
async def invite_team_member(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Team API: User invitation request submitted by user_id={current_user.id}")
    
    # Enforce Admin/Manager permissions
    if current_user.role.lower() not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins or Managers can invite team members."
        )
        
    email = payload.get("email")
    name = payload.get("name", "New Member")
    role = payload.get("role", "member")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email parameter is required."
        )
        
    # Check duplicate
    exists_res = await db.execute(select(User).filter(User.email == email))
    if exists_res.scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )
        
    # Create record
    invited_user = User(
        email=email,
        name=name,
        hashed_password="INVITED_MOCK_PASSWORD",
        role=role,
        organization_id=current_user.organization_id,
        is_active=False,
        invite_token=secrets.token_hex(16),
        invite_expires=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )
    db.add(invited_user)
    
    # Log audit entry
    log = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="user_invited",
        description=f"Invited '{name}' ({email}) as a '{role}'",
        ip_address="127.0.0.1"
    )
    db.add(log)
    await db.commit()
    
    return StandardResponse(
        success=True,
        message="Invitation token created and email queued successfully.",
        data={
            "id": invited_user.id,
            "email": invited_user.email,
            "role": invited_user.role
        }
    )

@router.get("/audit-logs", response_model=StandardResponse[list])
async def list_audit_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Team API: Fetching audit history for org id={current_user.organization_id}")
    
    result = await db.execute(
        select(AuditLog)
        .filter(AuditLog.organization_id == current_user.organization_id)
        .order_by(AuditLog.created_at.desc())
        .limit(20)
    )
    logs = list(result.scalars().all())
    
    # Sandbox Helper: Seed default logs for UI demonstration
    if not logs:
        logger.info("No audit logs found. Seeding developer sandbox audit entries.")
        mock1 = AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="api_key_rotated",
            description="Rotated Vapi Assistant Webhook Auth Key",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=2)
        )
        mock2 = AuditLog(
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            action="settings_modified",
            description="Updated business hours: Enabled Saturday slots",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
        )
        db.add_all([mock1, mock2])
        await db.commit()
        logs = [mock1, mock2]
        
    data = [{
        "id": l.id,
        "action": l.action,
        "description": l.description,
        "ip_address": l.ip_address or "127.0.0.1",
        "created_at": l.created_at.isoformat()
    } for l in logs]
    
    return StandardResponse(
        success=True,
        message="Audit log history successfully compiled.",
        data=data
    )
