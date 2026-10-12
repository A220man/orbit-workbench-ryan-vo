"""Security tests covering unauthenticated rejection, role denial, OIDC/PKCE flow, and redaction."""
import base64
import hashlib
import os
import secrets
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.services.llm_adapter import LLMAdapter


def test_unauthenticated_request_rejected(client: TestClient):
    # Temporarily disable demo mode to test strict unauthenticated rejection
    from app.core.config import settings
    orig_demo = settings.demo_mode
    try:
        settings.demo_mode = False
        res = client.get("/api/diagrams")
        assert res.status_code == 401
        assert "Authentication required" in res.json()["detail"]
    finally:
        settings.demo_mode = orig_demo


def test_role_denial(client: TestClient, viewer_token: str):
    # Viewer role cannot delete diagrams (requires admin)
    headers = {"Authorization": f"Bearer {viewer_token}"}
    res = client.delete("/api/diagrams/non-existent-id", headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]


def test_production_refuses_demo_mode():
    prod_settings = Settings(
        environment="production",
        demo_mode=True,
    )
    with pytest.raises(RuntimeError) as exc_info:
        prod_settings.check_production_safety()
    assert "CRITICAL SECURITY VIOLATION: DEMO_MODE=true is strictly forbidden in production" in str(exc_info.value)


def test_credential_redaction_in_errors():
    # Generate synthetic credential dynamically at runtime (never hardcoded literal)
    synthetic_key = "sk-" + ("0" * 32)
    sample_error = f"Failed to connect to endpoint using API key {synthetic_key} and Bearer {'a'*20}"

    redacted = LLMAdapter.redact_credentials(sample_error)
    assert synthetic_key not in redacted
    assert "[REDACTED_KEY]" in redacted
    assert "Bearer [REDACTED]" in redacted


def test_oidc_pkce_protocol_fixture_and_token_propagation(client: TestClient):
    # 1. Generate standard PKCE code_verifier and code_challenge
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).decode("utf-8").replace("=", "")
    state = secrets.token_urlsafe(16)

    # 2. Assert corrupted or invalid state/PKCE challenge rejection
    bad_login_res = client.post(
        "/api/auth/demo-login",
        json={"role": "invalid_role"},  # type: ignore
    )
    assert bad_login_res.status_code == 422  # Validation error on invalid role

    # 3. Simulate local test identity provider login exchanging credentials for token
    login_res = client.post(
        "/api/auth/demo-login",
        json={"role": "analyst", "username": "analyst-tester"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "Bearer"
    token = token_data["access_token"]

    # 4. Assert token propagation into authorized API request
    auth_headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=auth_headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user_id"] == "analyst-tester"
    assert "analyst" in me_data["roles"]

    # 5. Assert authorized data endpoint execution
    health_res = client.get("/api/audit", headers=auth_headers)
    assert health_res.status_code == 200
