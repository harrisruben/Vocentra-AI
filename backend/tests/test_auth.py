import pytest

@pytest.mark.asyncio
async def test_auth_pipeline(client):
    # 1. Test signup creation
    signup_data = {
        "email": "tester@vocentra.ai",
        "name": "Workspace Tester",
        "organization_name": "Test Organization Inc",
        "password": "securepassword99"
    }
    
    response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 201
    res_json = response.json()
    assert res_json["success"] is True
    assert "access_token" in res_json["data"]
    assert res_json["data"]["token_type"] == "bearer"
    
    # 2. Test duplicate email validation error
    dup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert dup_response.status_code == 400
    dup_json = dup_response.json()
    assert dup_json["success"] is False
    assert "exists" in dup_json["message"]

    # 3. Test successful login
    login_data = {
        "email": "tester@vocentra.ai",
        "password": "securepassword99"
    }
    login_response = await client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
    login_json = login_response.json()
    assert login_json["success"] is True
    token = login_json["data"]["access_token"]
    
    # 4. Test current user verification endpoint (/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_response = await client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    me_json = me_response.json()
    assert me_json["success"] is True
    assert me_json["data"]["email"] == "tester@vocentra.ai"
    assert me_json["data"]["name"] == "Workspace Tester"
    
    # 5. Test invalid token access handler
    bad_headers = {"Authorization": "Bearer fake_token_signature_string"}
    bad_response = await client.get("/api/v1/auth/me", headers=bad_headers)
    assert bad_response.status_code == 401
    bad_json = bad_response.json()
    assert bad_json["success"] is False
