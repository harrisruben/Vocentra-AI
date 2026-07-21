import hashlib
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import ApiKey, User
from app.schemas.schemas import StandardResponse
from app.api.deps import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/dashboard/keys", tags=["API Keys"])

@router.get("", response_model=StandardResponse[list])
async def list_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"API Keys API: Fetching keys list for org id={current_user.organization_id}")
    
    result = await db.execute(
        select(ApiKey).filter(
            ApiKey.organization_id == current_user.organization_id,
            ApiKey.is_active == True
        )
    )
    keys = list(result.scalars().all())
    
    # Sandbox Helper: Populate mock key details if none exist
    if not keys:
        logger.info("No API Keys found. Seeding developer sandbox API key.")
        mock_key = ApiKey(
            organization_id=current_user.organization_id,
            name="n8n Production Workflow Connector",
            key_prefix="sk_live_687c...",
            hashed_key=hashlib.sha256("mock_api_key_secret_code".encode()).hexdigest(),
            is_active=True
        )
        db.add(mock_key)
        await db.commit()
        keys = [mock_key]
        
    data = [{
        "id": k.id,
        "name": k.name,
        "key_prefix": k.key_prefix,
        "created_at": k.created_at.isoformat()
    } for k in keys]
    
    return StandardResponse(
        success=True,
        message="API Keys fetched successfully",
        data=data
    )

@router.post("", response_model=StandardResponse[dict])
async def create_key(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    name = payload.get("name", "New Developer Token")
    logger.info(f"API Keys API: Generating key name='{name}' for org={current_user.organization_id}")
    
    # Generate random key secret
    raw_token = "sk_live_" + secrets.token_hex(20)
    prefix = raw_token[:12] + "..."
    
    # Secure storage: hash the key using SHA-256
    hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
    
    new_key = ApiKey(
        organization_id=current_user.organization_id,
        name=name,
        key_prefix=prefix,
        hashed_key=hashed_token,
        is_active=True
    )
    db.add(new_key)
    await db.commit()
    
    return StandardResponse(
        success=True,
        message="Developer API Key successfully created. Copy and save this token now—it will not be shown again.",
        data={
            "id": new_key.id,
            "name": new_key.name,
            "key_prefix": new_key.key_prefix,
            "plain_key": raw_token
        }
    )

@router.delete("/{key_id}", response_model=StandardResponse[dict])
async def revoke_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    logger.info(f"API Keys API: Revoking key_id={key_id} for org={current_user.organization_id}")
    
    result = await db.execute(
        select(ApiKey).filter(
            ApiKey.id == key_id,
            ApiKey.organization_id == current_user.organization_id
        )
    )
    key = result.scalar()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )
        
    key.is_active = False
    await db.commit()
    
    return StandardResponse(
        success=True,
        message="API Key revoked successfully.",
        data={"id": key_id}
    )
