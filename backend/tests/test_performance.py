import asyncio
import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import get_db
from tests.conftest import TestingSessionLocal
from app.core.config import settings

@pytest.mark.asyncio
async def test_concurrent_call_webhooks_performance(db) -> None:
    """Simulate concurrent inbound call webhook requests and measure latency and throughput."""
    
    # Custom get_db override that provisions fresh session instances per concurrent request
    async def override_get_db_concurrency():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
                
    app.dependency_overrides[get_db] = override_get_db_concurrency
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        num_requests = 30
        
        # Inbound call Twilio payload simulation
        async def send_inbound_webhook(index: int):
            payload = {
                "CallSid": f"twilio_perf_test_sid_{index}",
                "From": f"+1555100{index:04d}",
                "To": "+18005550199",
                "CallStatus": "ringing"
            }
            start = time.time()
            response = await client.post("/api/v1/webhooks/twilio", data=payload)
            duration = time.time() - start
            return response, duration

        # Launch all requests concurrently
        start_time = time.time()
        results = await asyncio.gather(*(send_inbound_webhook(i) for i in range(num_requests)))
        total_duration = time.time() - start_time
        
        # Clear override
        app.dependency_overrides.clear()
        
        # Assertions
        latencies = [duration for res, duration in results]
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        # Log details
        print(f"\n--- Concurrent Telephony Webhook Performance (N={num_requests}) ---")
        print(f"Total time for N requests: {total_duration:.3f} seconds")
        print(f"Average request latency: {avg_latency * 1000:.1f} ms")
        print(f"Maximum request latency: {max_latency * 1000:.1f} ms")
        print(f"Throughput: {num_requests / total_duration:.1f} req/sec")
        
        for response, duration in results:
            assert response.status_code == 200
            # Verify XML response from Twilio
            assert "<Response>" in response.text

        # Dynamic budget based on database dialect (SQLite vs Postgres)
        is_sqlite = settings.DATABASE_URL.startswith("sqlite")
        latency_budget = 5.0 if is_sqlite else 0.150
        
        assert avg_latency < latency_budget, f"Average latency too high: {avg_latency*1000:.1f}ms (budget={latency_budget*1000:.1f}ms)"
