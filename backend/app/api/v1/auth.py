from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import ValidationError, AuthError
from app.models.models import User, Organization
from app.schemas.schemas import UserCreate, UserResponse, Token, UserLogin, StandardResponse
from app.api.deps import get_current_user
from app.core.logger import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=StandardResponse[Token], status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    logger.info(f"Attempting to register user: {user_in.email}")
    
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise ValidationError("A user with this email already exists.")
    
    # Create Organization
    org = Organization(name=user_in.organization_name)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    logger.info(f"Created organization {org.name} (id: {org.id})")
    
    # Create User
    hashed_pwd = hash_password(user_in.password)
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_pwd,
        role=user_in.role or "admin",
        organization_id=org.id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"Registered user {user.email} (id: {user.id})")
    
    # Create token
    access_token = create_access_token(data={"sub": user.email, "id": user.id, "organization_id": user.organization_id})
    token_data = Token(access_token=access_token, token_type="bearer")
    
    return StandardResponse(
        success=True,
        message="User workspace registered successfully",
        data=token_data
    )

@router.post("/login", response_model=StandardResponse[Token])
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    logger.info(f"Login attempt for user: {user_in.email}")
    result = await db.execute(select(User).filter(User.email == user_in.email))
    user = result.scalars().first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise AuthError("Incorrect email or password.")
        
    access_token = create_access_token(data={"sub": user.email, "id": user.id, "organization_id": user.organization_id})
    token_data = Token(access_token=access_token, token_type="bearer")
    
    logger.info(f"Successful login for user: {user.email}")
    return StandardResponse(
        success=True,
        message="Login successful",
        data=token_data
    )

@router.get("/me", response_model=StandardResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    user_res = UserResponse.model_validate(current_user)
    return StandardResponse(
        success=True,
        message="Current user context retrieved",
        data=user_res
    )
