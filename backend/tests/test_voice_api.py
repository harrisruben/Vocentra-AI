import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.models import Customer, User
from sqlalchemy.future import select

@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient):
    email = "lifecycle_admin@vocentra.ai"
    signup_data = {
        "email": email,
        "name": "Lifecycle Admin",
        "organization_name": "Lifecycle Enterprise Limited",
        "password": "adminpassword123"
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "adminpassword123"
    })
    token = login_resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_voice_call_lifecycle_endpoints(client: AsyncClient, db, admin_headers) -> None:
    # 1. Start Call
    start_payload = {
        "vapi_call_id": "vapi_test_lifecycle_id",
        "twilio_call_id": "twilio_test_lifecycle_sid",
        "customer_phone": "+15550199000"
    }
    response = await client.post("/api/v1/calls/start", json=start_payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "call_id" in res_data["data"]
    
    call_id = res_data["data"]["call_id"]
    
    # 2. Update Transcript (User message)
    transcript_payload = {
        "vapi_call_id": "vapi_test_lifecycle_id",
        "text": "Hello, I'd like to schedule a product consulting meeting.",
        "role": "user"
    }
    response = await client.post("/api/v1/calls/transcript", json=transcript_payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # 3. Update Call Status
    status_payload = {
        "vapi_call_id": "vapi_test_lifecycle_id",
        "status": "connected"
    }
    response = await client.post("/api/v1/calls/status", json=status_payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # 4. Fetch Call Details (GET /calls/{id}) - Proxied through VapiService
    response = await client.get(f"/api/v1/calls/{call_id}", headers=admin_headers)
    assert response.status_code == 200
    detail_data = response.json()
    assert detail_data["success"] is True
    assert detail_data["data"]["status"] == "ended"  # Vapi detail fallback state
    assert detail_data["data"]["summary"]
    assert detail_data["data"]["recordingUrl"]
    assert detail_data["data"]["transcript"]
    assert detail_data["data"]["analysis"]
    assert len(detail_data["data"]["messages"]) > 0
    assert detail_data["data"]["messages"][0]["content"] == "Hello, I'd like to schedule a product consulting meeting."
    
    # 5. Fetch Call History list (GET /calls) - Proxied through VapiService
    response = await client.get("/api/v1/calls", headers=admin_headers)
    assert response.status_code == 200
    history_data = response.json()
    assert history_data["success"] is True
    assert len(history_data["data"]) > 0
    
    # 6. End Call
    end_payload = {
        "vapi_call_id": "vapi_test_lifecycle_id",
        "twilio_call_id": "twilio_test_lifecycle_sid",
        "duration": 45,
        "recording_url": "http://example.com/recording.wav",
        "summary": "Customer requested scheduling info and scheduled a slot.",
        "transcript": "Hello, I'd like to schedule a product consulting meeting.",
        "cost": 0.35
    }
    response = await client.post("/api/v1/calls/end", json=end_payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

@pytest.mark.asyncio
async def test_analytics_metrics_endpoints(client: AsyncClient, admin_headers) -> None:
    # 1. Live analytics
    response = await client.get("/api/v1/analytics/live", headers=admin_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "active_calls" in res_data["data"]
    assert "intents_distribution" in res_data["data"]
    
    # 2. Cost analytics
    response = await client.get("/api/v1/analytics/cost", headers=admin_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "total_cost" in res_data["data"]
    
    # 3. Performance analytics
    response = await client.get("/api/v1/analytics/performance", headers=admin_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert "avg_llm_latency" in res_data["data"]


@pytest.mark.asyncio
async def test_call_delete_flow(client: AsyncClient, db) -> None:
    from app.models.models import Call, Customer, Organization
    from sqlalchemy.future import select

    # 1. Signup and login User A (Org A)
    signup_a = {
        "email": "c_user_a@vocentra.ai",
        "name": "Call User A",
        "organization_name": "Call Org A",
        "password": "password123"
    }
    await client.post("/api/v1/auth/signup", json=signup_a)
    login_a = await client.post("/api/v1/auth/login", json={"email": signup_a["email"], "password": signup_a["password"]})
    token_a = login_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Signup and login User B (Org B)
    signup_b = {
        "email": "c_user_b@vocentra.ai",
        "name": "Call User B",
        "organization_name": "Call Org B",
        "password": "password123"
    }
    await client.post("/api/v1/auth/signup", json=signup_b)
    login_b = await client.post("/api/v1/auth/login", json={"email": signup_b["email"], "password": signup_b["password"]})
    token_b = login_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Retrieve Org A and Org B from DB
    res_a = await db.execute(select(Organization).filter(Organization.name == "Call Org A"))
    org_a = res_a.scalar()
    res_b = await db.execute(select(Organization).filter(Organization.name == "Call Org B"))
    org_b = res_b.scalar()

    # 3. Create a Customer and Call record manually under Org A
    customer = Customer(
        name="Test Customer",
        phone="+15550199123",
        organization_id=org_a.id
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)

    call_record = Call(
        vapi_call_id="vapi_delete_test_id",
        twilio_call_id="twilio_delete_test_sid",
        organization_id=org_a.id,
        customer_id=customer.id,
        status="completed"
    )
    db.add(call_record)
    await db.commit()
    await db.refresh(call_record)
    
    call_id = call_record.id

    # 4. User B (Org B) tries to delete User A's call record -> should return 403 (Authentication stage)
    del_fail = await client.delete(f"/api/v1/calls/{call_id}", headers=headers_b)
    assert del_fail.status_code == 403
    assert del_fail.json()["stage"] == "Authentication"

    # 5. User A deletes non-existent call record -> 404 Database stage
    del_miss = await client.delete("/api/v1/calls/99999", headers=headers_a)
    assert del_miss.status_code == 404
    assert del_miss.json()["stage"] == "Database"

    # 6. User A deletes their call record successfully -> 200 success
    del_ok = await client.delete(f"/api/v1/calls/{call_id}", headers=headers_a)
    assert del_ok.status_code == 200
    assert del_ok.json()["success"] is True
