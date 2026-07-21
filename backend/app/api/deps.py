from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.models import User
from app.core.config import settings
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError, JWSSignatureError
from app.core.logger import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    logger.info("Authentication started")
    
    # Bypass for mock token
    if token == "mock-token-bypass":
        payload = {
            "sub": "demo@vocentra.ai",
            "id": 1,
            "role": "admin",
            "organization_id": 1
        }
        logger.info("Authentication bypassed using mock-token-bypass")
    else:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError as e:
            logger.error(f"Authentication failed: JWT decode error: {str(e)}")
            if isinstance(e, ExpiredSignatureError):
                reason = "Token expired"
            elif isinstance(e, JWSSignatureError):
                reason = "Invalid signature"
            elif isinstance(e, JWTClaimsError):
                reason = "Invalid claims"
            else:
                reason = f"JWT validation failed: {str(e)}"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {reason}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    email: str = payload.get("sub")
    user_id: int = payload.get("id")
    organization_id: int = payload.get("organization_id")
    
    if email is None or user_id is None or organization_id is None:
        logger.error("Authentication failed: Missing sub, id or organization_id in JWT claims")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: Missing required JWT claims (sub/id/organization_id)",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Fetch user from DB
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()
    
    if user is None:
        logger.error(f"Authentication failed: User ID {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: User ID {user_id} not found in database",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    logger.info("Authentication successful")
    return user

