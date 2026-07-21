import urllib.parse
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.logger import logger

# Parse redis settings safely
redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
try:
    parsed = urllib.parse.urlparse(redis_url)
    redis_host = parsed.hostname or "localhost"
    redis_port = parsed.port or 6379
except Exception:
    redis_host = "localhost"
    redis_port = 6379

async def startup(ctx) -> None:
    logger.info("ARQ: Background queue listener started successfully.")

async def shutdown(ctx) -> None:
    logger.info("ARQ: Background queue listener shut down.")

async def execute_background_job(ctx, task_name: str, payload: dict) -> dict:
    """Invoked asynchronously by background task runner."""
    logger.info(f"ARQ Worker: Processing background job '{task_name}' payload='{payload}'")
    if task_name == "process_campaign":
        from app.workers.campaign_worker import process_campaign
        campaign_id = payload.get("campaign_id")
        if campaign_id:
            await process_campaign(campaign_id)
            return {"status": "success", "campaign_id": campaign_id}
    return {"status": "success", "task_name": task_name}

class WorkerSettings:
    """Settings required by arq CLI to start the background worker process."""
    functions = [execute_background_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(host=redis_host, port=redis_port)
