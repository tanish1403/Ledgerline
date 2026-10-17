"""Unit tests for human approval workflow, separation of duties, rollback, and LangGraph pausing/resuming."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agents.workflow import create_approval_workflow
from api.db.inspection_models import InspectionFlag
from api.db.models import Base, Role, User
from api.db.session import get_db
from api.main import app


@pytest.fixture
def client_and_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    db = TestingSessionLocal()
    admin1 = User(username="admin_alice", role=Role.admin, password_hash="hash")
    admin2 = User(username="admin_bob", role=Role.admin, password_hash="hash")
    analyst1 = User(username="analyst_charlie", role=Role.analyst, password_hash="hash")
    db.add_all([admin1, admin2, analyst1])
    db.commit()
    db.close()

    yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    engine.dispose()


def test_workflow_pause_and_approve(client_and_db):
    client, SessionLocal = client_and_db

    workflow = create_approval_workflow()
    config = {"configurable": {"thread_id": "test_thread_1"}}

    initial_state = {
        "messages": [],
        "unit_ids": [101, 102],
        "reason": "High vibration anomaly",
        "flag_id": None,
        "status": "started",
    }
    result = workflow.invoke(initial_state, config)
    state = workflow.get_state(config)
    assert len(state.next) > 0
    assert "flag_inspection" in state.next


def test_approvals_api_endpoints(client_and_db):
    client, SessionLocal = client_and_db

    db = SessionLocal()
    flag = InspectionFlag(
        unit_ids='[201, 202]',
        reason='Thermal overload',
        status='requested',
        requested_by='agent_system',
        created_at='2026-10-16T00:00:00+00:00',
    )
    db.add(flag)
    db.commit()
    flag_id = flag.id
    db.close()

    response = client.get("/approvals", headers={"X-User": "admin_alice", "X-Role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1

    db = SessionLocal()
    flag2 = InspectionFlag(
        unit_ids='[301]',
        reason='Pressure spike',
        status='requested',
        requested_by='admin_alice',
        created_at='2026-10-16T00:00:00+00:00',
    )
    db.add(flag2)
    db.commit()
    flag2_id = flag2.id
    db.close()

    res_self = client.post(f"/approvals/{flag2_id}/approve", headers={"X-User": "admin_alice", "X-Role": "admin"})
    assert res_self.status_code == 403

    res_approve = client.post(f"/approvals/{flag_id}/approve", headers={"X-User": "admin_bob", "X-Role": "admin"})
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "applied"

    res_double = client.post(f"/approvals/{flag_id}/approve", headers={"X-User": "admin_bob", "X-Role": "admin"})
    assert res_double.status_code == 400

    res_rollback = client.post(f"/flags/{flag_id}/rollback", headers={"X-User": "admin_bob", "X-Role": "admin"})
    assert res_rollback.status_code == 200
    assert res_rollback.json()["status"] == "rolled_back"

"""Unit tests for human approval workflow, separation of duties, rollback, and LangGraph pausing/resuming."""

import pytest


@pytest.fixture
def client_and_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    db = TestingSessionLocal()
    # Create test users
    admin1 = User(username="admin_alice", role=Role.admin, password_hash="hash")
    admin2 = User(username="admin_bob", role=Role.admin, password_hash="hash")
    analyst1 = User(username="analyst_charlie", role=Role.analyst, password_hash="hash")
    db.add_all([admin1, admin2, analyst1])
    db.commit()
    db.close()

    yield client, TestingSessionLocal

    app.dependency_overrides.clear()
    engine.dispose()


def test_workflow_pause_and_approve(client_and_db):
    client, SessionLocal = client_and_db

    # Test LangGraph workflow pausing at interrupt_before=["flag_inspection"]
    workflow = create_approval_workflow()
    config = {"configurable": {"thread_id": "test_thread_1"}}

    # Initial invoke
    initial_state = {
        "messages": [],
        "unit_ids": [101, 102],
        "reason": "High vibration anomaly",
        "flag_id": None,
        "status": "started",
    }
    result = workflow.invoke(initial_state, config)

    # Graph should be interrupted at flag_inspection
    state = workflow.get_state(config)
    assert len(state.next) > 0
    assert "flag_inspection" in state.next

    # Resume graph by invoking with None (or approve via API which triggers action)
    # Let's test the API approval endpoint
    db = SessionLocal()
    flag = db.query(InspectionFlag).first()
    assert flag is not None
    assert flag.status == "requested"
    assert flag.requested_by == "agent"
    db.close()

    # Authenticate as admin_bob (different from requester "agent", so SOD passes)
    # Wait, how does auth work in tests? Let's check api/dependencies.py or headers.
    # In api/dependencies.py, require_role checks current user token or header. Let's inspect test_reliability.py or similar for how auth headers are passed.
