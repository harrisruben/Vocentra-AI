import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.logger import logger

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Sliding-window API Rate Limiter mapping client IPs with standardised envelopes."""
    
    def __init__(self, app, limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        # In-memory IP tracking cache (scales to Redis in production)
        self.request_history = {}

    async def dispatch(self, request: Request, call_next):
        # critical webhooks and health-checks bypass rate limiting to prevent drops
        bypass_paths = [
            "/health",
            "/api/v1/webhooks/twilio",
            "/api/v1/webhooks/vapi"
        ]
        
        if request.url.path in bypass_paths or request.url.path.startswith("/api/v1/webhooks"):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Clean request timestamps older than our current sliding window
        history = self.request_history.get(client_ip, [])
        history = [timestamp for timestamp in history if now - timestamp < self.window_seconds]
        
        if len(history) >= self.limit:
            logger.warning(f"RateLimiter: Blocked IP={client_ip} on path={request.url.path} (Limit={self.limit}/min)")
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "message": "Too many requests. Please wait a minute before retrying.",
                    "data": None
                }
            )
            
        # Register new timestamp
        history.append(now)
        self.request_history[client_ip] = history
        
        return await call_next(request)
