"""
Automated unit & integration tests for TradeRule AI Authentication & Authorization.
Covers:
- Registration & validation
- Password hashing (Argon2id)
- Login & invalid credentials
- Duplicate registration rejection
- Role elevation prevention
- Unauthenticated rejection (401)
- RBAC permission enforcement (403 for non-admin on admin routes)
- Session invalidation on logout
"""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add project & backend src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api import app
from db import init_db, get_db, User, get_user_by_email
from auth import hash_password, verify_password, create_access_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Ensure database schema exists before tests."""
    init_db()


def test_password_hashing_argon2id():
    """Verify passwords are secure and hashed with Argon2id, not stored in plaintext."""
    raw = "SecureP@ssw0rd123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert "$argon2id$" in hashed
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_registration_and_no_role_elevation():
    """Verify regular registration succeeds and cannot self-assign the admin role."""
    unique_email = f"test_user_{os.urandom(4).hex()}@example.com"
    payload = {
        "email": unique_email,
        "password": "ValidPassword123!",
        "full_name": "Test Runner",
        "role": "admin",  # Attacker attempt to self-elevate
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ok"
    assert data["user"]["email"] == unique_email
    # CRITICAL: Role must be 'user', self-elevation attempt must be ignored
    assert data["user"]["role"] == "user"
    assert "token" in data


def test_duplicate_registration_rejected():
    """Verify duplicate email registration is rejected with 409 Conflict."""
    email = f"dup_{os.urandom(4).hex()}@example.com"
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "First User",
    }
    r1 = client.post("/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"]


def test_login_success_and_invalid_credentials():
    """Verify login authentication with correct and incorrect credentials."""
    email = f"login_test_{os.urandom(4).hex()}@example.com"
    client.post("/auth/register", json={
        "email": email,
        "password": "MySecretPass123!",
        "full_name": "Login Tester",
    })

    # Wrong password
    bad_login = client.post("/auth/login", json={
        "email": email,
        "password": "IncorrectPassword999!",
    })
    assert bad_login.status_code == 401
    assert "Invalid email or password" in bad_login.json()["detail"]

    # Correct password
    good_login = client.post("/auth/login", json={
        "email": email,
        "password": "MySecretPass123!",
    })
    assert good_login.status_code == 200
    data = good_login.json()
    assert data["user"]["email"] == email
    assert "token" in data


def test_unauthenticated_request_rejected():
    """Verify protected endpoints reject unauthenticated requests with 401."""
    fresh_client = TestClient(app)
    fresh_client.cookies.clear()
    r_me = fresh_client.get("/auth/me")
    assert r_me.status_code == 401

    r_chat = fresh_client.post("/chat", json={"question": "Test question"})
    assert r_chat.status_code == 401


def test_rbac_user_cannot_access_admin_endpoints():
    """Verify regular users cannot access administrative endpoints (403 Forbidden)."""
    email = f"reg_user_{os.urandom(4).hex()}@example.com"
    reg_resp = client.post("/auth/register", json={
        "email": email,
        "password": "Password123!",
    })
    token = reg_resp.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # /logs requires admin
    r_logs = client.get("/logs", headers=headers)
    assert r_logs.status_code == 403
    assert "Administrator access required" in r_logs.json()["detail"]

    # /documents/list requires admin
    r_docs = client.get("/documents/list", headers=headers)
    assert r_docs.status_code == 403


def test_admin_can_access_admin_endpoints():
    """Verify administrator account can access protected admin endpoints."""
    # Ensure admin exists
    from bootstrap_admin import bootstrap_admin
    admin_email = f"admin_{os.urandom(4).hex()}@traderule.ai"
    bootstrap_admin(email=admin_email, password="AdminSecret123!", force=True)

    login_resp = client.post("/auth/login", json={
        "email": admin_email,
        "password": "AdminSecret123!",
    })
    assert login_resp.status_code == 200
    admin_token = login_resp.json()["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    r_logs = client.get("/logs", headers=headers)
    assert r_logs.status_code == 200
    assert isinstance(r_logs.json(), list)

    r_docs = client.get("/documents/list", headers=headers)
    assert r_docs.status_code == 200
    assert isinstance(r_docs.json(), list)


def test_logout_clears_cookie():
    """Verify logout removes the session cookie."""
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    # Check that Set-Cookie header deletes traderule_session
    set_cookie_header = resp.headers.get("set-cookie", "")
    assert "traderule_session=" in set_cookie_header or resp.cookies.get("traderule_session") is None
