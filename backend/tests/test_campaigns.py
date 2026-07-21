import io

import pytest
from openpyxl import Workbook


@pytest.mark.asyncio
async def test_campaign_upload_and_progress(client):
    signup_data = {
        "email": "campaign_tester@vocentra.ai",
        "name": "Campaign Tester",
        "organization_name": "Campaign Org",
        "password": "securepassword99"
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert signup_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": signup_data["email"], "password": signup_data["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    csv_content = b"name,phone,email\nAlice,+15551234567,alice@example.com\nBob,+15559876543,bob@example.com\n"

    upload_response = await client.post(
        "/api/v1/campaigns/upload",
        headers=headers,
        data={"campaign_name": "Launch Campaign", "description": "Outbound renovation leads"},
        files={"file": ("contacts.csv", csv_content, "text/csv")},
    )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["success"] is True
    assert payload["data"]["campaign_id"] is not None
    assert payload["data"]["lead_count"] == 2

    campaign_id = payload["data"]["campaign_id"]

    start_response = await client.post(f"/api/v1/campaigns/{campaign_id}/start", headers=headers)
    assert start_response.status_code == 200

    list_response = await client.get("/api/v1/campaigns", headers=headers)
    assert list_response.status_code == 200
    campaigns = list_response.json()["data"]
    assert len(campaigns) >= 1

    progress_response = await client.get(f"/api/v1/campaigns/{campaign_id}/progress", headers=headers)
    assert progress_response.status_code == 200
    progress_payload = progress_response.json()["data"]
    assert progress_payload["campaign"]["id"] == campaign_id
    assert len(progress_payload["leads"]) == 2


@pytest.mark.asyncio
async def test_campaign_excel_upload(client):
    signup_data = {
        "email": "excel_campaign_tester@vocentra.ai",
        "name": "Excel Campaign Tester",
        "organization_name": "Excel Campaign Org",
        "password": "securepassword99"
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert signup_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": signup_data["email"], "password": signup_data["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Contacts"
    sheet.append(["name", "phone", "email"])
    sheet.append(["Carol", "+15550000001", "carol@example.com"])
    sheet.append(["Derek", "+15550000002", "derek@example.com"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    upload_response = await client.post(
        "/api/v1/campaigns/upload",
        headers=headers,
        data={"campaign_name": "Excel Campaign", "description": "Workbook import"},
        files={"file": ("contacts.xlsx", buffer.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["success"] is True
    assert payload["data"]["lead_count"] == 2


@pytest.mark.asyncio
async def test_campaign_real_file_upload(client):
    signup_data = {
        "email": "real_campaign_tester@vocentra.ai",
        "name": "Real Campaign Tester",
        "organization_name": "Real Campaign Org",
        "password": "securepassword99"
    }
    signup_response = await client.post("/api/v1/auth/signup", json=signup_data)
    assert signup_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": signup_data["email"], "password": signup_data["password"]}
    )
    assert login_response.status_code == 200
    token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    import os
    file_path = r"C:\Users\harry\Downloads\Campaign of AI Voice calling.xlsx"
    with open(file_path, "rb") as f:
        file_content = f.read()

    upload_response = await client.post(
        "/api/v1/campaigns/upload",
        headers=headers,
        data={"campaign_name": "Real Excel Campaign", "description": "Real spreadsheet upload test"},
        files={"file": ("Campaign of AI Voice calling.xlsx", file_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert upload_response.status_code == 200
    payload = upload_response.json()
    assert payload["success"] is True
    assert payload["data"]["lead_count"] == 2
    campaign_id = payload["data"]["campaign_id"]

    # Start campaign (triggers outbound voice calls via mock voice provider during test)
    start_response = await client.post(f"/api/v1/campaigns/{campaign_id}/start", headers=headers)
    assert start_response.status_code == 200

    # Retrieve progress and check status of leads
    progress_response = await client.get(f"/api/v1/campaigns/{campaign_id}/progress", headers=headers)
    assert progress_response.status_code == 200
    progress_payload = progress_response.json()["data"]
    assert progress_payload["campaign"]["id"] == campaign_id
    assert len(progress_payload["leads"]) == 2
    for lead in progress_payload["leads"]:
        assert lead["phone"] in ["+9025110211", "+6382553003"]
        assert lead["status"] == "completed"


@pytest.mark.asyncio
async def test_campaign_delete_flow(client) -> None:
    # 1. Signup and login User A (Org A)
    signup_a = {
        "email": "user_a@vocentra.ai",
        "name": "User A",
        "organization_name": "Org A",
        "password": "password123"
    }
    await client.post("/api/v1/auth/signup", json=signup_a)
    login_a = await client.post("/api/v1/auth/login", json={"email": signup_a["email"], "password": signup_a["password"]})
    token_a = login_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Signup and login User B (Org B)
    signup_b = {
        "email": "user_b@vocentra.ai",
        "name": "User B",
        "organization_name": "Org B",
        "password": "password123"
    }
    await client.post("/api/v1/auth/signup", json=signup_b)
    login_b = await client.post("/api/v1/auth/login", json={"email": signup_b["email"], "password": signup_b["password"]})
    token_b = login_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A uploads a campaign
    csv_content = b"name,phone,email\nAlice,+15551234567,alice@example.com\n"
    upload_res = await client.post(
        "/api/v1/campaigns/upload",
        headers=headers_a,
        data={"campaign_name": "Org A Campaign", "description": "Private campaign"},
        files={"file": ("contacts.csv", csv_content, "text/csv")},
    )
    campaign_id = upload_res.json()["data"]["campaign_id"]

    # 4. User B tries to delete User A's campaign -> should fail with 403 (Authentication stage)
    del_fail = await client.delete(f"/api/v1/campaigns/{campaign_id}", headers=headers_b)
    assert del_fail.status_code == 403
    payload_fail = del_fail.json()
    assert payload_fail["success"] is False
    assert payload_fail["stage"] == "Authentication"

    # 5. User A deletes non-existent campaign -> should fail with 404 (Database stage)
    del_miss = await client.delete("/api/v1/campaigns/99999", headers=headers_a)
    assert del_miss.status_code == 404
    payload_miss = del_miss.json()
    assert payload_miss["success"] is False
    assert payload_miss["stage"] == "Database"

    # 6. User A successfully deletes their campaign -> 200 success
    del_ok = await client.delete(f"/api/v1/campaigns/{campaign_id}", headers=headers_a)
    assert del_ok.status_code == 200
    assert del_ok.json()["success"] is True

