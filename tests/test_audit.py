"""Unit tests for tamper-evident audit log, hash chain verification, redaction, and concurrency."""

import concurrent.futures

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.db.models import Base
from audit.chain import AuditChain, AuditEvent, redactor


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_redaction():
    payload = {
        "username": "alice",
        "password": "super-secret-password",
        "api_key": "sk-12345",
        "nested": {"token": "bearer-xyz", "public": "hello"},
    }
    redacted = redactor(payload)
    assert redacted["password"] == "[REDACTED]"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
    assert redacted["nested"]["public"] == "hello"


def test_audit_chain_verify(memory_db):
    chain = AuditChain(memory_db)
    ev1 = chain.append(event_type="login", actor_user_id="alice", actor_role="admin", inputs={"username": "alice"})
    ev2 = chain.append(event_type="agent_run", actor_user_id="alice", actor_role="admin", inputs={"prompt": "fit weibull"})

    valid, broken_id, err = chain.verify()
    assert valid is True
    assert broken_id is None
    assert err is None
    assert ev2.prev_hash == ev1.hash


def test_audit_chain_tamper_detection(memory_db):
    chain = AuditChain(memory_db)
    chain.append(event_type="login", actor_user_id="alice", actor_role="admin")
    chain.append(event_type="agent_run", actor_user_id="alice", actor_role="admin")

    # Tamper with row 1 directly
    ev1 = memory_db.get(AuditEvent, 1)
    ev1.resource = "tampered-resource"
    memory_db.commit()

    valid, broken_id, err = chain.verify()
    assert valid is False
    assert broken_id == 1
    assert "Hash mismatch" in err


def test_concurrent_appends():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    chain = AuditChain(session)

    def worker(i):
        local_session = Session()
        local_chain = AuditChain(local_session)
        local_chain.append(event_type=f"concurrent_{i}", actor_user_id=f"user_{i}")
        local_session.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(10)]
        concurrent.futures.wait(futures)

    valid, broken_id, err = chain.verify()
    assert valid is True
    session.close()
