import pytest

@pytest.mark.asyncio
async def test_dashboard_and_analytics(client):
    # 1. Unauthenticated request should fail
    resp_unauth = await client.get("/api/v1/dashboard")
    assert resp_unauth.status_code == 401
    
    # 2. Create account & login to get token
    signup_data = {
        "email": "dash_tester@vocentra.ai",
        "name": "Dash Tester",
        "organization_name": "Analytics test org",
        "password": "testpassword123"
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "dash_tester@vocentra.ai",
        "password": "testpassword123"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Verify authenticated dashboard retrieval
    resp_dash = await client.get("/api/v1/dashboard", headers=headers)
    assert resp_dash.status_code == 200
    data_dash = resp_dash.json()
    assert data_dash["success"] is True
    assert "today_calls" in data_dash["data"]
    assert "recent_calls" in data_dash["data"]
    assert len(data_dash["data"]["recent_calls"]) > 0 # verified sandbox widgets fallbacks
    
    # 4. Verify authenticated analytics chart datapoint retrieval
    resp_analytics = await client.get("/api/v1/dashboard/analytics", headers=headers)
    assert resp_analytics.status_code == 200
    data_analytics = resp_analytics.json()
    assert data_analytics["success"] is True
    assert len(data_analytics["data"]["calls_over_time"]) > 0
