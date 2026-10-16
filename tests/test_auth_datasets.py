"""Tests for Milestone 1: auth, RBAC, and datasets API.

Coverage:
- Login: success, wrong password, inactive user
- Token: expired, tampered
- /me
- /users: admin only
- /datasets: table-driven RBAC across all roles and HTTP methods
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from api.config import settings
from api.db.models import Dataset
from tests.conftest import auth_header, get_token

# ===========================================================================
# Auth: POST /auth/token
# ===========================================================================


def test_login_success(client, viewer):
    resp = client.post(
        "/auth/token", data={"username": "viewer@test.com", "password": "viewerpass"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body


def test_login_wrong_password(client, viewer):
    resp = client.post("/auth/token", data={"username": "viewer@test.com", "password": "WRONG"})
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/auth/token", data={"username": "nobody@test.com", "password": "x"})
    assert resp.status_code == 401


# ===========================================================================
# Token validation
# ===========================================================================


def test_expired_token_is_rejected(client, viewer):
    now = datetime.now(UTC)
    payload = {
        "sub": str(viewer.id),
        "role": viewer.role.value,
        "iat": now - timedelta(hours=2),
        "exp": now - timedelta(seconds=1),
    }
    expired = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    resp = client.get("/me", headers=auth_header(expired))
    assert resp.status_code == 401


def test_tampered_token_is_rejected(client, viewer):
    token = get_token(client, "viewer@test.com", "viewerpass")
    header, payload_seg, sig = token.rsplit(".", 2)
    bad_token = f"{header}.{payload_seg}.{'A' + sig[1:]}"
    resp = client.get("/me", headers=auth_header(bad_token))
    assert resp.status_code == 401


def test_no_token_returns_401(client):
    resp = client.get("/me")
    assert resp.status_code == 401


# ===========================================================================
# GET /me
# ===========================================================================


def test_me_returns_own_profile(client, analyst):
    token = get_token(client, "analyst@test.com", "analystpass")
    resp = client.get("/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "analyst@test.com"
    assert body["role"] == "analyst"
    assert "hashed_password" not in body


# ===========================================================================
# GET /users
# ===========================================================================


@pytest.mark.parametrize(
    "email,password,expected",
    [
        ("viewer@test.com", "viewerpass", 403),
        ("analyst@test.com", "analystpass", 403),
        ("admin@test.com", "adminpass", 200),
    ],
)
def test_list_users_role_enforcement(client, viewer, analyst, admin, email, password, expected):
    token = get_token(client, email, password)
    resp = client.get("/users", headers=auth_header(token))
    assert resp.status_code == expected


# ===========================================================================
# /datasets — table-driven RBAC
# ===========================================================================


@pytest.fixture()
def existing_dataset(db, analyst):
    """A dataset owned by analyst, used for PUT/DELETE tests."""
    ds = Dataset(name="DS-1", description="original", owner_id=analyst.id)
    db.add(ds)
    db.flush()
    return ds


_DATASETS_RBAC = [
    # (method, url_tpl,        body,             viewer, analyst, admin, no_tok)
    ("GET", "/datasets", None, 200, 200, 200, 401),
    ("GET", "/datasets/ID", None, 200, 200, 200, 401),
    ("POST", "/datasets", {"name": "New"}, 403, 201, 201, 401),
    ("PUT", "/datasets/ID", {"name": "Upd"}, 403, 200, 200, 401),
    ("DELETE", "/datasets/ID", None, 403, 403, 204, 401),
]


@pytest.mark.parametrize(
    "method,url_tpl,body,viewer_code,analyst_code,admin_code,no_token_code",
    _DATASETS_RBAC,
)
def test_datasets_rbac(
    client,
    viewer,
    analyst,
    admin,
    existing_dataset,
    method,
    url_tpl,
    body,
    viewer_code,
    analyst_code,
    admin_code,
    no_token_code,
):
    """Every role and no-token case is checked for every datasets endpoint."""
    url = url_tpl.replace("/ID", f"/{existing_dataset.id}")

    viewer_tok = get_token(client, "viewer@test.com", "viewerpass")
    analyst_tok = get_token(client, "analyst@test.com", "analystpass")
    admin_tok = get_token(client, "admin@test.com", "adminpass")

    def call(headers):
        return client.request(method, url, json=body, headers=headers)

    assert call(auth_header(viewer_tok)).status_code == viewer_code
    assert call(auth_header(analyst_tok)).status_code == analyst_code
    assert call(auth_header(admin_tok)).status_code == admin_code
    assert call({}).status_code == no_token_code


# ===========================================================================
# GET /ready
# ===========================================================================


def test_ready_returns_ok(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
