import pytest

@pytest.mark.asyncio
async def test_saas_features(client) -> None:
    """Verifies workflows configs, developer api keys, team invitations, and audit log histories."""
    # 1. Sign up and Login to generate Auth Headers
    signup_data = {
        "email": "saas_admin@vocentra.ai",
        "name": "SaaS Admin",
        "organization_name": "SaaS Enterprise Limited",
        "password": "saaspassword123"
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "saas_admin@vocentra.ai",
        "password": "saaspassword123"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Verify n8n Workflows listing & toggle
    wf_list = await client.get("/api/v1/dashboard/workflows", headers=headers)
    assert wf_list.status_code == 200
    wf_data = wf_list.json()
    assert wf_data["success"] is True
    assert len(wf_data["data"]) > 0
    
    # Toggle first workflow enabled/disabled state
    target_id = wf_data["data"][0]["id"]
    toggle_resp = await client.put(f"/api/v1/dashboard/workflows/{target_id}/toggle", headers=headers)
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["success"] is True
    
    # 3. Verify API Key generation & deletion
    key_create = await client.post(
        "/api/v1/dashboard/keys", 
        json={"name": "HubSpot Automation Key"}, 
        headers=headers
    )
    assert key_create.status_code == 200
    create_data = key_create.json()
    assert "plain_key" in create_data["data"]
    
    # Verify key prefix shows up in lists
    key_list = await client.get("/api/v1/dashboard/keys", headers=headers)
    assert key_list.status_code == 200
    assert len(key_list.json()["data"]) >= 1
    
    # Revoke key
    key_id = create_data["data"]["id"]
    revoke_resp = await client.delete(f"/api/v1/dashboard/keys/{key_id}", headers=headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["success"] is True
    
    # 4. Verify Team listing, invitation, and Audit Logging
    team_list = await client.get("/api/v1/dashboard/team", headers=headers)
    assert team_list.status_code == 200
    assert len(team_list.json()["data"]) >= 1
    
    # Invite a member (Owner/Manager role allows this)
    invite_resp = await client.post(
        "/api/v1/dashboard/team/invite",
        json={"email": "agent_new@vocentra.ai", "name": "Agent New", "role": "member"},
        headers=headers
    )
    assert invite_resp.status_code == 200
    assert invite_resp.json()["success"] is True
    
    # Verify audit logs record user_invited action
    audit_list = await client.get("/api/v1/dashboard/team/audit-logs", headers=headers)
    assert audit_list.status_code == 200
    assert len(audit_list.json()["data"]) >= 1

@pytest.mark.asyncio
async def test_new_saas_endpoints(client) -> None:
    """Verifies RAG documents list/upload, SaaS billing status/upgrade, and Workspace settings get/put endpoints."""
    # 1. Sign up and Login to generate Auth Headers
    signup_data = {
        "email": "saas_user2@vocentra.ai",
        "name": "SaaS Admin 2",
        "organization_name": "SaaS Enterprise Limited 2",
        "password": "saaspassword123"
    }
    await client.post("/api/v1/auth/signup", json=signup_data)
    
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "saas_user2@vocentra.ai",
        "password": "saaspassword123"
    })
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test Billing Status GET
    billing_status = await client.get("/api/v1/dashboard/billing", headers=headers)
    assert billing_status.status_code == 200
    assert billing_status.json()["data"]["billing_tier"] == "free"
    assert billing_status.json()["data"]["usage_limit"] == 100

    # 3. Test Billing PUT Upgrade
    billing_upgrade = await client.put(
        "/api/v1/dashboard/billing/upgrade", 
        json={"tier": "growth"}, 
        headers=headers
    )
    assert billing_upgrade.status_code == 200
    assert billing_upgrade.json()["data"]["billing_tier"] == "growth"
    assert billing_upgrade.json()["data"]["usage_limit"] == 1000

    # 4. Test Workspace Settings GET and PUT
    settings_get = await client.get("/api/v1/dashboard/settings", headers=headers)
    assert settings_get.status_code == 200
    assert settings_get.json()["data"]["twilio_sid"] == ""

    settings_put = await client.put(
        "/api/v1/dashboard/settings",
        json={
            "twilio_sid": "AC123456",
            "twilio_token": "token123",
            "vapi_assistant_id": "vapi-id-abc",
            "n8n_webhook_url": "https://n8n.webhook/vapi"
        },
        headers=headers
    )
    assert settings_put.status_code == 200
    assert settings_put.json()["data"]["twilio_sid"] == "AC123456"

    # Re-fetch to ensure persistence
    settings_refetch = await client.get("/api/v1/dashboard/settings", headers=headers)
    assert settings_refetch.json()["data"]["twilio_token"] == "token123"

    # 5. Test RAG Documents GET and POST upload
    rag_docs = await client.get("/api/v1/rag/documents", headers=headers)
    assert rag_docs.status_code == 200
    assert len(rag_docs.json()["data"]) == 0

    # Simulate file upload (bytes file)
    from io import BytesIO
    file_payload = {"file": ("pricing_guide.txt", BytesIO(b"Enterprise pricing is $1200 per month."), "text/plain")}
    rag_upload = await client.post(
        "/api/v1/rag/upload",
        files=file_payload,
        headers=headers
    )
    assert rag_upload.status_code == 200
    assert rag_upload.json()["data"]["filename"] == "pricing_guide.txt"

    # Re-fetch documents to assert it's listed
    rag_docs_refetch = await client.get("/api/v1/rag/documents", headers=headers)
    assert len(rag_docs_refetch.json()["data"]) == 1
    assert rag_docs_refetch.json()["data"][0]["title"] == "pricing_guide.txt"

    # 6. Test AI Health Center GET endpoint
    health_resp = await client.get("/api/v1/dashboard/health", headers=headers)
    assert health_resp.status_code == 200
    health_data = health_resp.json()["data"]
    assert "database" in health_data
    assert "redis" in health_data
    assert "vapi" in health_data
    assert "twilio" in health_data
    assert "websockets" in health_data
    assert "knowledge_base" in health_data
    assert health_data["database"]["status"] == "healthy"
    assert health_data["knowledge_base"]["document_count"] == 1

    # 7. Test Outbound Calling Trigger
    outbound_resp = await client.post(
        "/api/v1/calls/outbound",
        json={"customer_phone": "+15559876543", "customer_name": "Outbound Lead"},
        headers=headers
    )
    assert outbound_resp.status_code == 200
    outbound_data = outbound_resp.json()["data"]
    assert "vapi_call_id" in outbound_data
    vapi_call_id = outbound_data["vapi_call_id"]

    # Terminate the outbound call
    end_resp = await client.post(
        f"/api/v1/calls/{vapi_call_id}/end",
        headers=headers
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["data"]["success"] is True



