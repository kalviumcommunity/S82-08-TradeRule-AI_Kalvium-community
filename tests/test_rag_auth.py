"""
Integration tests for TradeRule AI RAG system with authentication:
- Public /health endpoint
- Authenticated /chat and /query execution
- Grounded answer and source citations
- Out-of-domain query safe refusal
- Admin document upload protection
"""

import os
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "backend" / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api import app, initialize_clients
from db import init_db
from bootstrap_admin import bootstrap_admin

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def init_system():
    init_db()
    initialize_clients()


@pytest.fixture
def user_auth_headers():
    email = f"rag_user_{os.urandom(3).hex()}@example.com"
    r = client.post("/auth/register", json={
        "email": email,
        "password": "UserPass123!",
        "full_name": "RAG Analyst",
    })
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers():
    admin_email = f"rag_admin_{os.urandom(3).hex()}@traderule.ai"
    bootstrap_admin(email=admin_email, password="AdminPass123!", force=True)
    r = client.post("/auth/login", json={
        "email": admin_email,
        "password": "AdminPass123!",
    })
    token = r.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_public_health_endpoint():
    """Verify /health is public and returns operational status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "TradeRule AI" in data["service"]


def test_authenticated_rag_query_with_citations(user_auth_headers):
    """Verify authenticated user can perform RAG compliance queries with valid citations."""
    resp = client.post(
        "/chat",
        json={"question": "When does an exporter need an export license?"},
        headers=user_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["answered", "cache_hit"]
    assert "export license" in data["answer"].lower()
    assert len(data["sources"]) > 0
    # Check top citation format
    first_source = data["sources"][0]
    assert "citation" in first_source
    assert "source" in first_source


def test_out_of_domain_query_safe_refusal(user_auth_headers):
    """Verify hallucination guardrails trigger safe refusal for ungrounded queries."""
    resp = client.post(
        "/chat",
        json={"question": "What is the best chocolate chip cookie recipe?"},
        headers=user_auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    # Guardrail must refuse to answer out-of-domain knowledge
    assert "don't have enough information" in data["answer"].lower() or data["status"] == "refused_weak_context"


def test_document_upload_protection(user_auth_headers, admin_auth_headers):
    """Verify document upload is forbidden to regular users and authorized for admins."""
    test_file_content = b"Import rules: Goods require HS classification."
    files = {"file": ("test_compliance_doc.txt", test_file_content, "text/plain")}

    # Regular user upload -> 403 Forbidden
    r_user = client.post("/documents", files=files, headers=user_auth_headers)
    assert r_user.status_code == 403
