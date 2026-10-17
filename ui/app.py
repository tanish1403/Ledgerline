"""Reliability Agent Platform - Streamlit Web Dashboard."""

import streamlit as st

from ui.views.agent_studio import render_agent_studio_view
from ui.views.analytics import render_analytics_view
from ui.views.approvals import render_approvals_view
from ui.views.audit import render_audit_view
from ui.views.rag_search import render_rag_view

# Streamlit Page Config
st.set_page_config(
    page_title="Reliability Agent Platform",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    # Sidebar
    with st.sidebar:
        st.title("⚙️ Reliability Agent")
        st.caption("Self-Hosted Autonomous Engineering Reliability Platform")
        st.divider()

        # Role switcher for RBAC demo
        st.subheader("👤 User Persona & RBAC")
        role_options = ["analyst", "approver", "admin"]
        selected_role = st.selectbox(
            "Active Role:",
            role_options,
            index=0,
            help="Switch role to test Role-Based Access Control and separation of duties.",
        )
        st.session_state["role"] = selected_role
        user_map = {
            "analyst": "sarah.analyst",
            "approver": "marcus.approver",
            "admin": "elena.admin",
        }
        active_user = user_map.get(selected_role, "user.demo")
        st.caption(f"Authenticated as: `{active_user}`")

        st.divider()

        # Navigation menu
        st.subheader("🧭 Navigation")
        nav_selection = st.radio(
            "Select Workspace:",
            [
                "🧠 Agent Studio",
                "📊 Reliability Analytics",
                "🚦 Human Approvals",
                "🛡️ Tamper-Evident Audit",
                "📚 RAG Knowledge Base",
            ],
            index=0,
        )

        st.divider()
        st.caption("Stack: Python 3.11+ | FastAPI | LangGraph | PostgreSQL | Celery | Redis")

    # Dispatch to appropriate view
    if nav_selection == "🧠 Agent Studio":
        render_agent_studio_view(current_role=selected_role)
    elif nav_selection == "📊 Reliability Analytics":
        render_analytics_view()
    elif nav_selection == "🚦 Human Approvals":
        render_approvals_view(current_user=active_user, current_role=selected_role)
    elif nav_selection == "🛡️ Tamper-Evident Audit":
        render_audit_view()
    elif nav_selection == "📚 RAG Knowledge Base":
        render_rag_view(current_role=selected_role)


if __name__ == "__main__":
    main()
