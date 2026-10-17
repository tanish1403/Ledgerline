"""Tamper-Evident Hash-Chained Audit Trail View."""

import json
from typing import Any

import streamlit as st

from audit.chain import compute_hash


def _generate_mock_chain() -> list[dict[str, Any]]:
    """Generate representative hash-chained events."""
    raw_events = [
        {
            "id": 1,
            "actor_user_id": "sarah.analyst",
            "actor_role": "analyst",
            "event_type": "dataset.query",
            "resource": "turbofan_dataset_1",
            "inputs": {"dataset_id": 1, "limit": 100},
            "outputs": {"row_count": 100},
            "trace_id": "tr-001",
            "timestamp": "2026-10-17T08:00:00Z",
        },
        {
            "id": 2,
            "actor_user_id": "sarah.analyst",
            "actor_role": "analyst",
            "event_type": "weibull.fit",
            "resource": "turbofan_dataset_1",
            "inputs": {"durations": [112.0, 145.0, 166.0], "api_key": "[REDACTED]"},
            "outputs": {"shape": 2.45, "scale": 268.1},
            "trace_id": "tr-002",
            "timestamp": "2026-10-17T08:05:00Z",
        },
        {
            "id": 3,
            "actor_user_id": "sarah.analyst",
            "actor_role": "analyst",
            "event_type": "inspection.flag_request",
            "resource": "unit-102",
            "inputs": {"units": ["102", "108"], "reason": "MAD outlier"},
            "outputs": {"status": "requested", "flag_id": 1},
            "trace_id": "tr-003",
            "timestamp": "2026-10-17T09:30:00Z",
        },
        {
            "id": 4,
            "actor_user_id": "elena.admin",
            "actor_role": "admin",
            "event_type": "inspection.flag_approval",
            "resource": "unit-102",
            "inputs": {"flag_id": 1, "approved": True},
            "outputs": {"status": "approved"},
            "trace_id": "tr-004",
            "timestamp": "2026-10-17T09:35:00Z",
        },
    ]

    events = []
    prev_h = "0" * 64
    for ev in raw_events:
        item = dict(ev)
        item["inputs"] = json.dumps(item["inputs"])
        item["outputs"] = json.dumps(item["outputs"])
        item["prev_hash"] = prev_h
        h = compute_hash(prev_h, item)
        item["hash"] = h
        events.append(item)
        prev_h = h
    return events


def render_audit_view() -> None:
    st.header("🛡️ Tamper-Evident Audit Trail")
    st.caption(
        "Cryptographically chained audit events (SHA-256) with zero-knowledge secret redaction."
    )

    if "audit_events" not in st.session_state:
        st.session_state.audit_events = _generate_mock_chain()

    events = st.session_state.audit_events

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        if st.button(
            "🔍 Verify Cryptographic Chain Integrity", use_container_width=True, type="primary"
        ):
            # Walk chain and verify
            expected_prev = "0" * 64
            broken = False
            for ev in events:
                if ev["prev_hash"] != expected_prev:
                    st.error(
                        f"❌ Chain broken at Event #{ev['id']}: "
                        f"Expected {expected_prev[:12]}..., got {ev['prev_hash'][:12]}..."
                    )
                    broken = True
                    break
                ev_clean = {k: v for k, v in ev.items() if k != "hash"}
                calc_h = compute_hash(ev["prev_hash"], ev_clean)
                if calc_h != ev["hash"]:
                    st.error(
                        f"❌ Hash mismatch at Event #{ev['id']}! "
                        f"Expected {calc_h[:12]}..., found {ev['hash'][:12]}..."
                    )
                    broken = True
                    break
                expected_prev = ev["hash"]

            if not broken:
                st.success(
                    f"✅ Cryptographic Integrity Verified! All {len(events)} events "
                    "form an unbroken SHA-256 chain."
                )

    with col_btn2:
        if st.button("Simulate Data Tampering Attack", use_container_width=True):
            if events:
                # Tamper with event 2 outputs
                events[1]["outputs"] = json.dumps({"shape": 9.99, "tampered": True})
                st.warning(
                    "⚠️ Injected unauthorized modification into Event #2! "
                    "Click 'Verify' to test tamper detection."
                )

    st.divider()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        types = ["All"] + sorted(list({e["event_type"] for e in events}))
        selected_type = st.selectbox("Filter by Event Type:", types)
    with col_f2:
        actors = ["All"] + sorted(list({e["actor_user_id"] for e in events}))
        selected_actor = st.selectbox("Filter by Actor:", actors)

    filtered = events
    if selected_type != "All":
        filtered = [e for e in filtered if e["event_type"] == selected_type]
    if selected_actor != "All":
        filtered = [e for e in filtered if e["actor_user_id"] == selected_actor]

    # Display timeline
    for ev in reversed(filtered):
        ev_title = (
            f"Event #{ev['id']} | `{ev['event_type']}` | "
            f"{ev['actor_user_id']} ({ev['actor_role']}) - {ev['timestamp']}"
        )
        with st.expander(ev_title):
            hash_info = (
                f"Hash:      {ev['hash']}\n"
                f"Prev Hash: {ev['prev_hash']}\n"
                f"Trace ID:  {ev['trace_id']}"
            )
            st.code(hash_info, language="text")
            col_in, col_out = st.columns(2)
            with col_in:
                st.write("**Inputs (Redacted):**")
                st.json(json.loads(ev["inputs"]) if ev["inputs"] else {})
            with col_out:
                st.write("**Outputs:**")
                st.json(json.loads(ev["outputs"]) if ev["outputs"] else {})
