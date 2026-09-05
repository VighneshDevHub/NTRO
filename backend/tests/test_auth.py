import pytest

DRIVE_ERASE_REPORT = {
    "operation_type": "DRIVE_ERASE",
    "target_description": "SSD-AUTH-TEST-001",
    "started_at": "2026-08-30T10:00:00Z",
    "completed_at": "2026-08-30T10:00:05Z",
    "success": True,
    "operator": "someone-claiming-to-be-anyone",  # deliberately suspicious — must be ignored
    "details": {"method": "NIST 800-88 Clear"},
}


async def _register_and_login(client, email="investigator@forensicguard.example", password="supersecret123"):
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_register_creates_user(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@forensicguard.example", "password": "supersecret123"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@forensicguard.example", "password": "supersecret123"}
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password(client):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@forensicguard.example", "password": "correcthorse123"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@forensicguard.example", "password": "totally-wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_operation_requires_auth(client):
    """THE core Phase 5 fix: submitting a record without a token must
    now be rejected — this was the flagged 'anyone can call the API'
    gap."""
    resp = await client.post("/api/v1/operations", json=DRIVE_ERASE_REPORT)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_operation_rejects_garbage_token(client):
    resp = await client.post(
        "/api/v1/operations", json=DRIVE_ERASE_REPORT,
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_submit_operation_succeeds_with_valid_token(client):
    token = await _register_and_login(client)

    resp = await client.post(
        "/api/v1/operations", json=DRIVE_ERASE_REPORT,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_operator_field_is_overridden_by_authenticated_identity_not_client_input(client):
    """THE important security test: the client claimed operator =
    'someone-claiming-to-be-anyone' in the request body — the stored
    record must show the REAL authenticated user's email instead,
    proving the operator field can no longer be spoofed."""
    token = await _register_and_login(client, email="real.investigator@forensicguard.example")

    resp = await client.post(
        "/api/v1/operations", json=DRIVE_ERASE_REPORT,
        headers={"Authorization": f"Bearer {token}"},
    )
    body = resp.json()
    assert body["operator"] == "real.investigator@forensicguard.example"
    assert body["operator"] != "someone-claiming-to-be-anyone"


@pytest.mark.asyncio
async def test_verify_and_get_remain_public_without_auth(client):
    """Verification must stay public — that's the whole point of
    independent, no-login-required trust checking."""
    token = await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/operations", json=DRIVE_ERASE_REPORT,
        headers={"Authorization": f"Bearer {token}"},
    )
    cert_id = create_resp.json()["certificate_id"]

    get_resp = await client.get(f"/api/v1/operations/{cert_id}")  # no auth header
    assert get_resp.status_code == 200

    verify_resp = await client.get(f"/api/v1/verify/{cert_id}")  # no auth header
    assert verify_resp.status_code == 200
    assert verify_resp.json()["overall_verified"] is True
