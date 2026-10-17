"""Human Approval Gate View."""

from datetime import UTC, datetime

import streamlit as st

# In-memory mock store for demo if DB is empty or offline
MOCK_APPROVALS = [
    {
        "id": 1,
        "unit_ids": ["turbofan-102", "turbofan-108"],
        "reason": "Anomalous vibration harmonics detected above 3.5 MAD threshold.",
        "status": "requested",
        "requested_by": "analyst-sarah",
        "decided_by": None,
        "created_at": "2026-10-17T09:30:00Z",
        "decided_at": None,
        "applied_at": None,
        "rolled_back_at": None,
    },
    {
        "id": 2,
        "unit_ids": ["turbofan-205"],
        "reason": "Turbine inlet temperature sensor drift detected during cruise cycles.",
        "status": "requested",
        "requested_by": "analyst-john",
        "decided_by": None,
        "created_at": "2026-10-17T10:15:00Z",
        "decided_at": None,
        "applied_at": None,
        "rolled_back_at": None,
    },
    {
        "id": 3,
        "unit_ids": ["turbofan-044"],
        "reason": "Low cycle fatigue limit reached (>350 operational cycles).",
        "status": "approved",
        "requested_by": "analyst-sarah",
        "decided_by": "admin-elena",
        "created_at": "2026-10-16T14:00:00Z",
        "decided_at": "2026-10-16T14:20:00Z",
        "applied_at": "2026-10-16T14:22:00Z",
        "rolled_back_at": None,
    },
]


def render_approvals_view(current_user: str = "admin-demo", current_role: str = "admin") -> None:
    st.header("🚦 Human-in-the-Loop Approval Gate")
    st.caption(
        "Review, approve, or reject high-impact operational changes "
        "(e.g. equipment grounding and inspection flags)."
    )

    # Separation of duties badge
    st.info(
        f"Logged in as: **{current_user}** (Role: `{current_role}`) | "
        "*Separation of Duties enforced: Requesters cannot approve their own requests.*"
    )

    if "approvals_data" not in st.session_state:
        st.session_state.approvals_data = list(MOCK_APPROVALS)

    approvals = st.session_state.approvals_data

    # Filter tabs
    status_filter = st.radio(
        "Status Filter:", ["All", "Pending (requested)", "Approved", "Rejected"], horizontal=True
    )

    filtered = approvals
    if status_filter == "Pending (requested)":
        filtered = [a for a in approvals if a["status"] == "requested"]
    elif status_filter == "Approved":
        filtered = [a for a in approvals if a["status"] == "approved"]
    elif status_filter == "Rejected":
        filtered = [a for a in approvals if a["status"] == "rejected"]

    # Metrics
    col1, col2, col3 = st.columns(3)
    pending_cnt = sum(1 for a in approvals if a["status"] == "requested")
    col1.metric("Pending Approvals", pending_cnt)
    col2.metric("Total Flags", len(approvals))
    col3.metric(
        "Your Role Permission",
        "Can Approve/Reject" if current_role in ["admin", "approver"] else "View Only",
    )

    st.divider()

    if not filtered:
        st.success("No inspection flags matching the selected filter.")
        return

    for item in filtered:
        status_color = (
            "orange"
            if item["status"] == "requested"
            else ("green" if item["status"] == "approved" else "red")
        )
        with st.container():
            u_str = ", ".join(item["unit_ids"])
            status_tag = item["status"].upper()
            st.markdown(f"### Flag #{item['id']}: Units `{u_str}` :{status_color}[[{status_tag}]]")
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"**Reason:** {item['reason']}")
                st.write(f"**Requested by:** `{item['requested_by']}` at {item['created_at']}")
                if item["decided_by"]:
                    st.write(f"**Decided by:** `{item['decided_by']}` at {item['decided_at']}")
            with col_b:
                if item["status"] == "requested":
                    # Separation of duties check
                    is_requester = item["requested_by"] == current_user
                    can_decide = current_role in ["admin", "approver"]

                    if is_requester:
                        st.warning("⚠️ Cannot self-approve.")
                    elif not can_decide:
                        st.info("🔒 Requires admin/approver role.")
                    else:
                        c_app, c_rej = st.columns(2)
                        with c_app:
                            if st.button("✅ Approve", key=f"app_{item['id']}"):
                                item["status"] = "approved"
                                item["decided_by"] = current_user
                                item["decided_at"] = datetime.now(UTC).isoformat()
                                item["applied_at"] = datetime.now(UTC).isoformat()
                                st.success(f"Flag #{item['id']} approved!")
                                st.rerun()
                        with c_rej:
                            if st.button("❌ Reject", key=f"rej_{item['id']}"):
                                item["status"] = "rejected"
                                item["decided_by"] = current_user
                                item["decided_at"] = datetime.now(UTC).isoformat()
                                st.error(f"Flag #{item['id']} rejected.")
                                st.rerun()
                elif item["status"] == "approved":
                    if current_role in ["admin", "approver"] and not item.get("rolled_back_at"):
                        if st.button("⏪ Rollback Flag", key=f"roll_{item['id']}"):
                            item["status"] = "rolled_back"
                            item["rolled_back_at"] = datetime.now(UTC).isoformat()
                            st.warning(f"Flag #{item['id']} rolled back.")
                            st.rerun()

            st.divider()
