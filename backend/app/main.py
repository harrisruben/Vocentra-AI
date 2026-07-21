import uuid
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logger import logger, request_id_var
from app.core.exceptions import register_exception_handlers
from app.api.v1 import auth, keys, team, billing, settings as workspace_settings, outbound_calls, campaigns
from app.dashboard import dashboard, workflows
from app.voice.twilio import twilio
from app.voice.vapi import vapi
from app.voice import calls
from app.voice.websocket import websocket
from app.analytics import router as analytics
from app.events import register_all_subscribers
from app.ai.rag import router as rag
from app.core.rate_limiter import RateLimitingMiddleware

async def seed_users():
    from app.core.database import AsyncSessionLocal
    from app.models.models import User, Organization
    from app.core.security import hash_password
    from sqlalchemy.future import select

    async with AsyncSessionLocal() as db:
        # Check if default org exists
        result = await db.execute(select(Organization).filter(Organization.name == "Vocentra Org"))
        org = result.scalars().first()
        if not org:
            org = Organization(name="Vocentra Org", billing_tier="enterprise", usage_limit=1000000)
            db.add(org)
            await db.commit()
            await db.refresh(org)
            logger.info(f"Seeded default organization: Vocentra Org (id: {org.id})")

        # Admin user
        result = await db.execute(select(User).filter(User.email == "admin@vocentra.ai"))
        admin = result.scalars().first()
        if not admin:
            admin = User(
                email="admin@vocentra.ai",
                name="Admin User",
                hashed_password=hash_password("Password123"),
                role="admin",
                organization_id=org.id
            )
            db.add(admin)
            logger.info("Seeding default admin user: admin@vocentra.ai")

        # Normal user
        result = await db.execute(select(User).filter(User.email == "user@vocentra.ai"))
        normal_user = result.scalars().first()
        if not normal_user:
            normal_user = User(
                email="user@vocentra.ai",
                name="Normal User",
                hashed_password=hash_password("Password123"),
                role="member",
                organization_id=org.id
            )
            db.add(normal_user)
            logger.info("Seeding default normal user: user@vocentra.ai")

        await db.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Relies on Alembic for migrations in production/development
    logger.info(f"Starting Vocentra AI API in {settings.ENVIRONMENT} mode")
    register_all_subscribers()
    try:
        await seed_users()
    except Exception as e:
        logger.error(f"Error seeding database users on startup: {str(e)}")
    yield
    logger.info("Stopping Vocentra AI API")

app = FastAPI(
    title="Vocentra AI API",
    description="The backend engine powering Vocentra AI voice agents, webhooks, and analytics.",
    version="1.0.0",
    lifespan=lifespan
)

from prometheus_fastapi_instrumentator import Instrumentator
# Instrument FastAPI app to collect request latency and status metrics
Instrumentator().instrument(app)

@app.get("/metrics")
async def metrics(request: Request):
    if settings.ENVIRONMENT == "production":
        token = request.headers.get("X-Metrics-Token")
        if not token or token != settings.JWT_SECRET:
            return Response("Forbidden", status_code=403, media_type="text/plain")
            
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Connect custom exception handling wrappers
register_exception_handlers(app)

# Request ID logging middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    # Pull request id or generate new one
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    # Trace ID across threads
    token = request_id_var.set(req_id)
    
    start_time = time.time()
    logger.info(f"Incoming Request: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"Completed Request: {request.method} {request.url.path} (status: {response.status_code}, duration: {duration:.4f}s)")
        response.headers["X-Request-ID"] = req_id
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Failed Request: {request.method} {request.url.path} (error: {str(e)}, duration: {duration:.4f}s)")
        raise
    finally:
        request_id_var.reset(token)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitingMiddleware, limit=60, window_seconds=60)

# Version 2 Router Registrations
app.include_router(auth.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(keys.router, prefix="/api/v1")
app.include_router(team.router, prefix="/api/v1")
app.include_router(billing.router, prefix="/api/v1")
app.include_router(workspace_settings.router, prefix="/api/v1")
app.include_router(outbound_calls.router, prefix="/api/v1")
app.include_router(campaigns.router, prefix="/api/v1")

# Modular voice/analytics Router Registrations
app.include_router(twilio.router, prefix="/api/v1")
app.include_router(vapi.router, prefix="/api/v1")
app.include_router(calls.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
