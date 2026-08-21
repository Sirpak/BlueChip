"""Plan / role entitlement matrix."""

from fastapi.testclient import TestClient

from app.auth.entitlements import has_entitlement
from app.auth.seed import seed_dev_users
from app.main import app
from db.session import get_session_factory


def _client() -> TestClient:
    session = get_session_factory()()
    try:
        seed_dev_users(session)
    finally:
        session.close()
    return TestClient(app)


def test_entitlement_aliases() -> None:
    assert has_entitlement("USER", "PRO", "models_full")
    assert has_entitlement("USER", "PRO", "models_basic")
    assert not has_entitlement("USER", "FREE", "models_full")
    assert has_entitlement("ADMIN", "INTERNAL", "exports")


def test_free_user_matrix() -> None:
    client = _client()
    login = client.post("/api/auth/login", json={"username": "demo_free", "password": "demoFree123"})
    assert login.status_code == 200
    body = login.json()
    assert body["plan"] == "FREE"
    assert client.get("/games/upcoming").status_code == 200
    assert client.get("/api/models/candidate").status_code == 403
    assert client.get("/api/admin/health").status_code == 403
    assert client.get("/api/markets/price").status_code == 403
    assert client.get("/api/backtests/export").status_code == 403
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["usage"]["ask_queries_limit"] == 10


def test_pro_user_matrix() -> None:
    client = _client()
    login = client.post("/api/auth/login", json={"username": "demo_pro", "password": "demoPro123"})
    assert login.status_code == 200
    assert client.get("/api/models/candidate").status_code == 200
    assert client.get("/api/models/leaderboard").status_code == 200
    assert client.get("/api/research/deep").status_code == 403
    assert client.get("/api/backtests/export").status_code == 403
    assert client.get("/api/admin/health").status_code == 403


def test_research_user_matrix() -> None:
    client = _client()
    login = client.post("/api/auth/login", json={"username": "demo_research", "password": "demoResearch123"})
    assert login.status_code == 200
    assert client.get("/api/research/deep").status_code == 200
    assert client.get("/api/backtests/export").status_code == 200
    assert client.get("/api/admin/health").status_code == 403


def test_admin_matrix() -> None:
    client = _client()
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200
    assert login.json()["plan"] == "INTERNAL"
    assert client.get("/api/admin/health").status_code == 200
    assert client.get("/api/admin/pipeline").status_code == 200
    assert client.get("/api/backtests/export").status_code == 200
    unauth = TestClient(app)
    assert unauth.get("/games/upcoming").status_code == 401


def test_ask_quota_counts() -> None:
    client = _client()
    client.post("/api/auth/login", json={"username": "demo_free", "password": "demoFree123"})
    first = client.post("/api/ask/query", json={"question": "What is Ridge?"})
    assert first.status_code == 200
    assert first.json()["usage"]["ask_queries_used"] >= 1
