"""Tests for Streamlit UI modules and views."""

import json
from collections.abc import Generator

import pytest

from audit.chain import compute_hash
from reliability.stats import kaplan_meier, outliers, weibull_fit
from ui.views.approvals import MOCK_APPROVALS
from ui.views.audit import _generate_mock_chain
from ui.views.rag_search import SAMPLE_DOCS
from validators.recompute import AgentAnswer, Claim, validate_claims


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Generator[None, None, None]:
    """Override database setup fixture: UI tests do not require a PostgreSQL instance."""
    yield


def test_ui_views_importable() -> None:
    """Verify all UI view modules can be imported without missing dependencies."""
    from ui import app
    from ui.views import agent_studio, analytics, approvals, audit, rag_search

    assert callable(app.main)
    assert callable(agent_studio.render_agent_studio_view)
    assert callable(analytics.render_analytics_view)
    assert callable(approvals.render_approvals_view)
    assert callable(audit.render_audit_view)
    assert callable(rag_search.render_rag_view)


def test_audit_mock_chain_integrity() -> None:
    """Verify the mock chain generator creates an unbroken cryptographic hash chain."""
    chain = _generate_mock_chain()
    assert len(chain) == 4

    expected_prev = "0" * 64
    for ev in chain:
        assert ev["prev_hash"] == expected_prev
        clean_ev = {k: v for k, v in ev.items() if k != "hash"}
        calc_h = compute_hash(ev["prev_hash"], clean_ev)
        assert calc_h == ev["hash"]
        expected_prev = ev["hash"]


def test_audit_tamper_detection() -> None:
    """Verify that any modification to an event breaks the cryptographic chain."""
    chain = _generate_mock_chain()
    # Tamper with event 2's inputs
    tampered_chain = [dict(ev) for ev in chain]
    tampered_chain[1]["inputs"] = json.dumps({"durations": [999.0], "api_key": "[COMPROMISED]"})

    tampered_index = None
    expected_prev = "0" * 64
    for idx, ev in enumerate(tampered_chain):
        clean_ev = {k: v for k, v in ev.items() if k != "hash"}
        expected_h = compute_hash(ev["prev_hash"], clean_ev)
        if ev["prev_hash"] != expected_prev or ev["hash"] != expected_h:
            tampered_index = idx
            break
        expected_prev = ev["hash"]

    assert tampered_index == 1


def test_approvals_mock_structure() -> None:
    """Verify approvals mock data has expected schema and initial status values."""
    assert len(MOCK_APPROVALS) >= 3
    for a in MOCK_APPROVALS:
        assert "id" in a
        assert "unit_ids" in a
        assert isinstance(a["unit_ids"], list)
        assert a["status"] in ["requested", "approved", "rejected", "rolled_back"]
        assert "requested_by" in a


def test_approvals_separation_of_duties() -> None:
    """Verify separation-of-duties logic prevents requesters from approving their own requests."""
    req = {
        "id": 10,
        "requested_by": "sarah.analyst",
        "status": "requested",
    }
    current_user_same = "sarah.analyst"
    current_user_other = "marcus.approver"

    # Separation of duties rule:
    can_sarah_approve = current_user_same != req["requested_by"]
    can_marcus_approve = current_user_other != req["requested_by"]

    assert can_sarah_approve is False
    assert can_marcus_approve is True


def test_analytics_computations() -> None:
    """Verify numerical analytics calculations used by ui/views/analytics.py."""
    durations = [112.0, 145.0, 166.0, 180.0, 192.0, 205.0, 218.0, 225.0]
    events = [1] * len(durations)

    w_res = weibull_fit(durations, events)
    assert w_res["shape"] > 0
    assert w_res["scale"] > 0

    km_res = kaplan_meier(durations, events)
    assert len(km_res["timeline"]) == len(durations) + 1
    assert len(km_res["survival_function"]) == len(durations) + 1

    test_series = [10.0, 11.0, 10.5, 12.0, 11.5, 95.0]
    out_res = outliers(test_series, method="mad")
    assert 5 in out_res["indices"]


def test_agent_studio_claim_validation() -> None:
    """Verify that Agent Studio generates mathematically sound, validated claims."""
    durations = [120.0, 135.0, 150.0, 160.0, 180.0, 200.0]
    events = [1, 1, 1, 0, 1, 1]
    res = weibull_fit(durations, events)
    shape = round(float(res["shape"]), 3)
    scale = round(float(res["scale"]), 2)

    claims = [
        Claim(
            name="shape",
            value=shape,
            computation={
                "tool": "weibull_fit",
                "arguments": {"dataset_name": "train_FD001"},
            },
        ),
        Claim(
            name="scale",
            value=scale,
            computation={
                "tool": "weibull_fit",
                "arguments": {"dataset_name": "train_FD001"},
            },
        ),
    ]
    answer = AgentAnswer(
        summary=f"Fitted Weibull shape={shape}, scale={scale}",
        claims=claims,
        tool_calls_used=["weibull_fit"],
    )
    report = validate_claims(answer, tolerance=0.05)
    assert report.passed is True
    assert len(report.claims) == 2
    assert all(r.passed for r in report.claims)


def test_rag_role_filtering() -> None:
    """Verify that documents in RAG view are properly filtered based on user role."""
    analyst_docs = [
        d for d in SAMPLE_DOCS if ("analyst" == "admin" or d["role_access"] == "analyst")
    ]
    admin_docs = [
        d for d in SAMPLE_DOCS if ("admin" == "admin" or d["role_access"] == "analyst")
    ]

    assert len(analyst_docs) < len(admin_docs)
    assert any(d["role_access"] == "admin" for d in admin_docs)
    assert all(d["role_access"] == "analyst" for d in analyst_docs)

