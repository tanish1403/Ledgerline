"""Hybrid RAG Documentation Search Explorer View."""


import streamlit as st

SAMPLE_DOCS = [
    {
        "id": 1,
        "filename": "turbofan_maintenance_manual_fd001.pdf",
        "page": 42,
        "role_access": "analyst",
        "sim": 0.89,
        "rrf_score": 0.032,
        "text": (
            "Section 4.3 - HPC Inspection Criteria: Inspect compressor rotor blades "
            "for high-cycle fatigue microcracks when operational cycles exceed 200. "
            "Stage 5 or 6 blades with thermal discoloration must undergo ultrasonic testing."
        ),
    },
    {
        "id": 2,
        "filename": "weibull_analysis_guidelines_navy_mil_hdbk.pdf",
        "page": 17,
        "role_access": "analyst",
        "sim": 0.84,
        "rrf_score": 0.028,
        "text": (
            "Characteristic Life (η): The scale parameter represents the point at which "
            "63.2% of the population has failed. For beta > 1.0, the failure rate increases "
            "with operational duration, indicating wear-out requiring scheduled replacement."
        ),
    },
    {
        "id": 3,
        "filename": "standard_operating_procedures_flight_readiness.pdf",
        "page": 5,
        "role_access": "admin",
        "sim": 0.76,
        "rrf_score": 0.019,
        "text": (
            "Grounding and Inspection Protocols: Any turbofan unit flagged for vibration "
            "anomalies (>3.5 MAD) must be placed on maintenance hold pending sign-off "
            "by a certified reliability administrator with dual-party verification."
        ),
    },
]


def render_rag_view(current_role: str = "analyst") -> None:
    st.header("📚 Hybrid RAG Search Explorer")
    st.caption(
        "Dense vector similarity + BM25 full-text search fused with Reciprocal Rank Fusion (RRF)."
    )

    preset = st.selectbox(
        "Try a sample engineering query:",
        [
            "Custom Query",
            "When should turbofan compressor blades undergo ultrasonic non-destructive testing?",
            "How is the Weibull scale parameter η interpreted in reliability wear-out?",
            "What is the protocol for grounding units flagged with vibration anomalies?",
        ],
    )

    query = st.text_input(
        "Enter technical inquiry:",
        value="" if preset == "Custom Query" else preset,
        placeholder="e.g. What are the inspection guidelines for turbine blades?",
    )

    if not query:
        st.info(
            "Enter a query or select a preset to search the engineering documentation repository."
        )
        return

    st.subheader("Hybrid Retrieval Results (RRF Fused)")

    # Filter documents by role
    allowed_docs = [
        d for d in SAMPLE_DOCS if (current_role == "admin" or d["role_access"] == "analyst")
    ]

    for doc in allowed_docs:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"📄 **{doc['filename']}** (Page {doc['page']})")
                st.write(doc["text"])
            with col2:
                st.metric("Vector Similarity", f"{doc['sim'] * 100:.1f}%")
                st.caption(f"RRF Rank Score: `{doc['rrf_score']:.4f}`")
                st.caption(f"Role Access: `{doc['role_access']}`")
            st.divider()

    st.subheader("🤖 Synthesized Technical Answer")
    if "ultrasonic" in query.lower() or "compressor" in query.lower():
        st.markdown(
            "> HPC rotor blades must undergo ultrasonic non-destructive testing "
            "when operational cycles exceed **200**, specifically for stages 5 or 6 "
            "exhibiting thermal discoloration ([turbofan_maintenance_manual_fd001.pdf, p.42])."
        )
        st.success("Citations: `turbofan_maintenance_manual_fd001.pdf#page=42` | Confidence: 0.94")
    elif "weibull" in query.lower() or "scale" in query.lower() or "wear-out" in query.lower():
        st.markdown(
            "> The Weibull scale parameter (η) represents characteristic life where "
            "**63.2%** of the fleet fails. When shape β > 1.0, failure rate increases "
            "over time (wear-out phase), mandating scheduled replacement."
        )
        st.success("Citations: `weibull_guidelines_mil_hdbk.pdf#page=17` | Conf: 0.96")
    elif (
        "grounding" in query.lower() or "protocol" in query.lower() or "vibration" in query.lower()
    ):
        st.markdown(
            "> Turbofan units flagged for vibration anomalies (>3.5 MAD) must be placed on "
            "maintenance hold pending sign-off by a certified reliability administrator "
            "under dual-party verification protocols."
        )
        st.success("Citations: `sop_flight_readiness.pdf#page=5` | Conf: 0.91")
    else:
        st.info("Demonstration synthesis generated for technical document search.")
