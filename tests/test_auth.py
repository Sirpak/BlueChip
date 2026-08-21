"""Local authentication."""

from fastapi.testclient import TestClient

from app.auth.seed import seed_dev_users
from app.main import app
from db.session import get_session_factory


def test_login_and_admin_forbidden_for_demo() -> None:
    session = get_session_factory()()
    try:
        seed_dev_users(session)
    finally:
        session.close()

    client = TestClient(app)
    bad = client.post("/api/auth/login", json={"username": "demo_free", "password": "wrong"})
    assert bad.status_code == 401

    ok = client.post("/api/auth/login", json={"username": "demo_free", "password": "demoFree123"})
    assert ok.status_code == 200
    assert ok.json()["role"] == "USER"
    assert ok.json()["plan"] == "FREE"

    admin_health = client.get("/api/admin/health")
    assert admin_health.status_code == 403

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["username"] == "demo_free"

    slate = client.get("/games/upcoming")
    assert slate.status_code == 200


def test_admin_login_can_access_admin_health() -> None:
    session = get_session_factory()()
    try:
        seed_dev_users(session)
    finally:
        session.close()

    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login.status_code == 200

    health = client.get("/api/admin/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    unauth = TestClient(app)
    assert unauth.get("/games/upcoming").status_code == 401
