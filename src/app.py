import os

import requests
import streamlit as st


# --------------------------------------------------
# Configuration
# --------------------------------------------------

API_BASE_URL = os.getenv(
    "FINGUARD_API_URL",
    "http://127.0.0.1:8000",
).rstrip("/")

API_TIMEOUT = float(os.getenv("FINGUARD_API_TIMEOUT", "60"))

st.set_page_config(
    page_title="FinGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Theme and custom styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    /* Page and top toolbar share the same soft gradient.
       This removes the white strip above the page heading. */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    header[data-testid="stHeader"] {
        background: linear-gradient(
            135deg,
            #e8edff 0%,
            #e5eaf2 48%,
            #d5deeb 100%
        ) !important;
    }

    [data-testid="stMain"] > div {
        background: transparent !important;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2.8rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(
            160deg,
            #101827 0%,
            #1e293b 55%,
            #334155 100%
        ) !important;
        border-right: 1px solid rgba(148, 163, 184, 0.22);
    }

    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #f8fafc !important;
    }

    .sidebar-brand {
        color: #ffffff;
        font-size: 1.35rem;
        font-weight: 800;
        letter-spacing: -0.4px;
        margin: 0 0 4px 0;
    }

    .sidebar-caption {
        color: #aebbd0 !important;
        font-size: 0.82rem;
        margin-bottom: 1.1rem;
    }

    .backend-url-box {
        background: #0b1220;
        color: #f8fafc;
        border: 1px solid #475569;
        border-radius: 9px;
        padding: 11px 12px;
        font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
        font-size: 0.76rem;
        line-height: 1.5;
        overflow-wrap: anywhere;
        margin: 0.25rem 0 0.65rem 0;
    }

    .tools-title {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 750;
        margin: 0.2rem 0 0.75rem 0;
    }

    .tool-category {
        color: #94a3b8;
        font-size: 0.66rem;
        font-weight: 800;
        letter-spacing: 1.15px;
        margin: 0.9rem 0 0.42rem 0;
    }

    .tools-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
    }

    .tool-chip {
        display: inline-block;
        color: #eaf2ff;
        background: rgba(148, 163, 184, 0.14);
        border: 1px solid rgba(148, 163, 184, 0.30);
        border-radius: 7px;
        padding: 5px 8px;
        font-size: 0.72rem;
        font-weight: 600;
        line-height: 1.35;
    }

    .sidebar-note {
        color: #aebbd0 !important;
        font-size: 0.76rem;
        line-height: 1.65;
    }

    /* Animated heading */
    .rainbow-heading {
        display: inline-block;
        margin: 0.25rem 0 0.65rem 0;
        font-size: clamp(2.15rem, 4vw, 3.25rem);
        font-weight: 900;
        letter-spacing: -1.7px;
        line-height: 1.22;
        background: linear-gradient(
            90deg,
            #ff8a00,
            #ffd000,
            #8bd500,
            #00b979,
            #168bff,
            #8b5cf6,
            #ec4899,
            #ff8a00
        );
        background-size: 300% auto;
        color: transparent;
        -webkit-background-clip: text;
        background-clip: text;
        animation: rainbowFlow 8s linear infinite;
    }

    @keyframes rainbowFlow {
        from { background-position: 0% center; }
        to { background-position: 300% center; }
    }

    .dashboard-subtitle {
        color: #334155 !important;
        font-size: 1rem;
        line-height: 1.75;
        margin: 0 0 1.1rem 0;
    }

    /* Headings and general text */
    .stApp h1,
    .stApp h2,
    .stApp h3 {
        color: #111827 !important;
        font-weight: 800 !important;
    }

    .stApp p,
    .stApp label,
    .stApp [data-testid="stMarkdownContainer"] {
        color: #1e293b;
    }

    /* Forms and metric cards */
    [data-testid="stForm"],
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.78) !important;
        border: 1px solid rgba(255, 255, 255, 0.95) !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
    }

    [data-testid="stForm"] {
        padding: 14px !important;
    }

    [data-testid="stMetric"] {
        padding: 16px !important;
    }

    /* Orange accent line on dashboard cards and boxes */
    [data-testid="stForm"],
    [data-testid="stMetric"],
    [data-testid="stAlert"],
    [data-testid="stExpander"] {
        border-top: 3px solid #f97316 !important;
    }

    /* Centered developer credit */
    .developer-credit {
        text-align: center !important;
        color: #475569 !important;
        font-size: 0.88rem;
        font-weight: 650;
        letter-spacing: 0.2px;
        padding: 1.1rem 0 0.4rem 0;
        width: 100%;
    }

    /* Inputs */
    .stNumberInput input,
    .stTextInput input,
    .stSelectbox [data-baseweb="select"] {
        color: #111827 !important;
        background: #ffffff !important;
        border-radius: 9px !important;
    }

    /* Buttons: explicitly style both button and nested label */
    .stApp button[kind="primary"],
    .stApp button[kind="secondary"],
    .stApp [data-testid="stBaseButton-primary"],
    .stApp [data-testid="stBaseButton-secondary"] {
        background: linear-gradient(100deg, #111827, #334155) !important;
        border: 0 !important;
        border-radius: 9px !important;
        min-height: 2.55rem;
    }

    .stApp button[kind="primary"] *,
    .stApp button[kind="secondary"] *,
    .stApp [data-testid="stBaseButton-primary"] *,
    .stApp [data-testid="stBaseButton-secondary"] * {
        color: #ffffff !important;
        opacity: 1 !important;
    }

    .stApp button[kind="primary"]:hover,
    .stApp button[kind="secondary"]:hover,
    .stApp [data-testid="stBaseButton-primary"]:hover,
    .stApp [data-testid="stBaseButton-secondary"]:hover {
        background: linear-gradient(100deg, #4338ca, #7c3aed) !important;
        transform: translateY(-1px);
        transition: all 0.2s ease;
    }

    /* Status and separators */
    hr {
        border-color: rgba(100, 116, 139, 0.25) !important;
    }

    @media (max-width: 700px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            padding-top: 1.6rem !important;
        }

        .rainbow-heading {
            letter-spacing: -1px;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        .rainbow-heading {
            animation: none;
        }
    }

    /* Backend health success message */
[data-testid="stAlert"][data-baseweb="notification"] {
    background: #dcfce7 !important;
    border: 1px solid #86efac !important;
    border-top: 3px solid #f97316 !important;
    border-radius: 10px !important;
    color: #14532d !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {
    color: #14532d !important;
    font-weight: 600 !important;
}

/* Sidebar health-check button */
[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(110deg, #111827, #334155) !important;
    color: #ffffff !important;
    border: 1px solid #475569 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] .stButton button:hover {
    border-color: #f97316 !important;
    color: #ffffff !important;
}

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# API helper functions
# --------------------------------------------------

def api_request(method, endpoint, **kwargs):
    """Send an HTTP request to the FastAPI backend."""
    try:
        response = requests.request(
            method,
            f"{API_BASE_URL}{endpoint}",
            timeout=API_TIMEOUT,
            **kwargs,
        )
        response.raise_for_status()

        try:
            return response.json()
        except ValueError:
            st.error("The backend returned an invalid JSON response.")
            return None

    except requests.exceptions.HTTPError:
        try:
            body = response.json()
            detail = body.get("detail", response.text)
        except (ValueError, AttributeError):
            detail = response.text

        st.error(f"API error ({response.status_code}): {detail}")

    except requests.exceptions.Timeout:
        st.error(f"The API request timed out after {API_TIMEOUT:g} seconds.")

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to FastAPI. "
            "Check that the backend is running and the URL is correct."
        )

    except requests.exceptions.RequestException as exc:
        st.error(f"API request failed: {exc}")

    return None


def display_risk(risk):
    """Display rule-based risk analysis."""
    if not risk:
        st.warning("Risk analysis is unavailable.")
        return

    col1, col2, col3 = st.columns(3)

    col1.metric("Risk Score", f"{risk.get('risk_score', 0)}/100")
    col2.metric("Risk Level", risk.get("risk_level", "UNKNOWN"))
    col3.metric(
        "Review Required",
        "Yes" if risk.get("requires_review") else "No",
    )

    st.subheader("Detected Risk Signals")
    signals = risk.get("signals", [])

    if signals:
        for signal in signals:
            with st.expander(signal.get("signal", "Risk signal")):
                st.write(signal.get("description", ""))
                st.write(f"Risk points: {signal.get('points', 0)}")
    else:
        st.info("No rule-based risk signals detected.")

    disclaimer = risk.get("disclaimer")
    if disclaimer:
        st.caption(disclaimer)


def display_report(report):
    """Display the generated investigation report."""
    st.subheader("Investigation Report")

    if report:
        st.markdown(report)
    else:
        st.info("No investigation report is available yet.")


# --------------------------------------------------
# Sidebar: configuration and tools stack
# --------------------------------------------------

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">🛡️ FinGuard AI</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="sidebar-caption">Transaction Investigation Platform</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("System Configuration")
    st.caption("Backend URL")

    st.markdown(
        f'<div class="backend-url-box">{API_BASE_URL}</div>',
        unsafe_allow_html=True,
    )

    if st.button("Check Backend Health", key="sidebar_health", use_container_width=True):
        health_check = api_request("GET", "/api/v1/health")
        if health_check:
            st.success(f"Connected: {health_check.get('service', 'API')}")

    st.divider()

    st.markdown(
        """
        <div class="tools-title">⚙️ Tools Stack</div>

        <div class="tool-category">PROGRAMMING</div>
        <div class="tools-row">
            <span class="tool-chip">Python</span>
        </div>

        <div class="tool-category">BACKEND & UI</div>
        <div class="tools-row">
            <span class="tool-chip">FastAPI</span>
            <span class="tool-chip">Streamlit</span>
        </div>

        <div class="tool-category">AGENTIC AI</div>
        <div class="tools-row">
            <span class="tool-chip">LangChain</span>
            <span class="tool-chip">LangGraph</span>
            <span class="tool-chip">Gemini</span>
        </div>

        <div class="tool-category">RAG & RETRIEVAL</div>
        <div class="tools-row">
            <span class="tool-chip">ChromaDB</span>
            <span class="tool-chip">BM25</span>
            <span class="tool-chip">RRF</span>
            <span class="tool-chip">FlashRank</span>
        </div>

        <div class="tool-category">DATABASE</div>
        <div class="tools-row">
            <span class="tool-chip">SQLite</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        '<div class="sidebar-note">'
        'AI-assisted investigation with rule-based risk analysis '
        'and human oversight.'
        '</div>',
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# Main dashboard header and backend health
# --------------------------------------------------

st.markdown(
    '<div class="rainbow-heading">🛡️ FinGuard AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="dashboard-subtitle">
        Financial Investigation &amp; Risk Intelligence Platform<br>
        Investigate transactions &bull; Analyze risk &bull;
        Review evidence &bull; Manage cases
    </div>
    """,
    unsafe_allow_html=True,
)

health = api_request("GET", "/api/v1/health")

if health:
    st.success(f"Backend connected — {health.get('service', 'API')}")
else:
    st.warning("Backend connection is unavailable. Check the sidebar URL and API server.")

st.divider()


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "investigation" not in st.session_state:
    st.session_state.investigation = None

if "case" not in st.session_state:
    st.session_state.case = None


# --------------------------------------------------
# 1. Start investigation
# --------------------------------------------------

st.header("Start New Investigation")

with st.form("investigation_form"):
    transaction_id = st.number_input(
        "Transaction ID",
        min_value=1,
        step=1,
    )

    start_clicked = st.form_submit_button(
        "🔎 Start Investigation",
        type="primary",
        use_container_width=True,
    )

if start_clicked:
    result = api_request(
        "POST",
        "/api/v1/investigations",
        json={"transaction_id": int(transaction_id)},
    )

    if result:
        st.session_state.investigation = result
        st.session_state.case = None
        st.success("Investigation started successfully.")


# --------------------------------------------------
# 2. Display investigation
# --------------------------------------------------

investigation = st.session_state.investigation

if investigation:
    st.divider()
    st.header("Investigation Results")

    col1, col2 = st.columns(2)
    col1.write(f"**Transaction ID:** {investigation.get('transaction_id')}")
    col2.write(f"**Workflow Status:** {investigation.get('status')}")

    st.write(f"**Case ID:** {investigation.get('case_id') or 'Not created'}")
    display_risk(investigation.get("risk_analysis"))

    # --------------------------------------------------
    # 3. Human review
    # --------------------------------------------------

    if investigation.get("human_review_required"):
        st.divider()
        st.header("Human Review")

        st.warning(
            "Human review is required before this workflow can complete."
        )
        st.write(
            "Inspect the transaction details and risk signals before "
            "submitting a decision."
        )

        decision = st.selectbox(
            "Select your decision",
            ["APPROVED", "REJECTED", "ESCALATED"],
        )

        if st.button(
            "Submit Human Decision",
            type="primary",
            use_container_width=True,
        ):
            thread_id = investigation.get("thread_id")

            if not thread_id:
                st.error("Workflow thread ID is missing.")
            else:
                result = api_request(
                    "POST",
                    "/api/v1/investigations/decision",
                    json={
                        "thread_id": thread_id,
                        "decision": decision,
                    },
                )

                if result:
                    st.session_state.investigation = result
                    st.success("Human decision recorded successfully.")
                    st.rerun()
    else:
        st.success("No pending human review.")

    st.divider()
    display_report(investigation.get("report"))


# --------------------------------------------------
# 4. Retrieve existing investigation case
# --------------------------------------------------

st.divider()
st.header("Investigation Case History")

with st.form("case_form"):
    case_id = st.number_input(
        "Enter an existing Case ID",
        min_value=1,
        step=1,
        key="case_id_input",
    )

    retrieve_clicked = st.form_submit_button(
    "Retrieve Case",
    type="primary",
    use_container_width=True,
)

if retrieve_clicked:
    result = api_request(
        "GET",
        f"/api/v1/cases/{int(case_id)}",
    )

    if result:
        st.session_state.case = result


# --------------------------------------------------
# 5. Display case details
# --------------------------------------------------

case = st.session_state.case

if case:
    st.subheader(f"Case #{case.get('id')}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Score", case.get("risk_score", 0))
    col2.metric("Risk Level", case.get("risk_level", "UNKNOWN"))
    col3.metric("Status", case.get("status", "UNKNOWN"))

    st.write("**Human Decision:**", case.get("human_decision"))

    if case.get("signals"):
        st.write("**Risk Signals:**")
        st.json(case["signals"])

    display_report(case.get("investigation_report"))

    with st.expander("Complete Case Record"):
        st.json(case)


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()
st.caption(
    "FinGuard AI | Preliminary heuristic risk assessment. "
    "Risk scores are not calibrated fraud probabilities. "
    "The system does not independently establish fraud or authorize "
    "account freezes or payment reversals."
)

st.markdown(
    '<div class="developer-credit">'
    'Developed by Khaja Mainuddin | Artificial Intelligence &amp; Data Science'
    '</div>',
    unsafe_allow_html=True,
)
