import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import WorkflowConfig, User
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/dashboard/workflows", tags=["Workflows"])

@router.get("", response_model=StandardResponse[list])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Workflows API: Listing integrations for org id={current_user.organization_id}")
    
    result = await db.execute(
        select(WorkflowConfig).filter(WorkflowConfig.organization_id == current_user.organization_id)
    )
    configs = list(result.scalars().all())
    
    # Sandbox Helper: Populate mock n8n automation configurations if none exist
    if not configs:
        logger.info("No workflow configuration detected. Provisioning mock workflows.")
        mock1 = WorkflowConfig(
            organization_id=current_user.organization_id,
            name="HubSpot CRM Qualification Sync",
            webhook_url="https://n8n.vocentra.ai/webhook/twilio-lead-sync",
            enabled=True,
            last_status="success",
            last_executed_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        )
        mock2 = WorkflowConfig(
            organization_id=current_user.organization_id,
            name="Resend Scheduler Email Notification",
            webhook_url="https://n8n.vocentra.ai/webhook/vapi-booking-notify",
            enabled=True,
            last_status="success",
            last_executed_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=10)
        )
        mock3 = WorkflowConfig(
            organization_id=current_user.organization_id,
            name="Slack Operations Alert Channel",
            webhook_url="https://n8n.vocentra.ai/webhook/slack-channel-alert",
            enabled=False,
            last_status="failed",
            last_executed_at=datetime.datetime.utcnow() - datetime.timedelta(days=2)
        )
        db.add_all([mock1, mock2, mock3])
        await db.commit()
        configs = [mock1, mock2, mock3]
        
    data = [{
        "id": c.id,
        "name": c.name,
        "webhook_url": c.webhook_url,
        "enabled": c.enabled,
        "retries": c.retries,
        "last_status": c.last_status,
        "last_executed_at": c.last_executed_at.isoformat() if c.last_executed_at else None
    } for c in configs]
    
    return StandardResponse(
        success=True,
        message="Workflows fetched successfully",
        data=data
    )

@router.put("/{config_id}/toggle", response_model=StandardResponse[dict])
async def toggle_workflow(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"Workflows API: Toggling state for config_id={config_id}")
    
    result = await db.execute(
        select(WorkflowConfig).filter(
            WorkflowConfig.id == config_id,
            WorkflowConfig.organization_id == current_user.organization_id
        )
    )
    config = result.scalar()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow configuration not found"
        )
        
    config.enabled = not config.enabled
    await db.commit()
    
    return StandardResponse(
        success=True,
        message=f"Workflow '{config.name}' successfully {'enabled' if config.enabled else 'disabled'}.",
        data={"id": config.id, "enabled": config.enabled}
    )
