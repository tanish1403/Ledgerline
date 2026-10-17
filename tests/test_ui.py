"""Tests for Streamlit UI modules and views."""

from audit.chain import compute_hash
from ui.views.audit import _generate_mock_chain


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


def test_approvals_mock_structure() -> None:
    """Verify approvals mock data has expected schema and initial status values."""
    from ui.views.approvals import MOCK_APPROVALS

    assert len(MOCK_APPROVALS) >= 3
    for a in MOCK_APPROVALS:
        assert "id" in a
        assert "unit_ids" in a
        assert isinstance(a["unit_ids"], list)
        assert a["status"] in ["requested", "approved", "rejected", "rolled_back"]
