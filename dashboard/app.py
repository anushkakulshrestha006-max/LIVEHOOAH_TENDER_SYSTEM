from datetime import datetime, date
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from dashboard_data import (
    build_dashboard_metrics,
    build_data_quality_metrics,
    build_daily_run_audit,
    build_deadline_distribution,
    build_opportunity_trend,
    build_priority_distribution,
    build_qualification_trend,
    filter_opportunities,
    get_deadline_status,
    load_activity_log,
    load_opportunities,
    sort_opportunities_by_deadline,
)


st.set_page_config(
    page_title="LIVEHOOAH | Tender Intelligence",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ================================================================
# Institutional Design System & Typography
# ================================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        color-scheme: light !important;
        --font-main: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        --font-mono: 'JetBrains Mono', monospace;
        --bg-page: #f8fafc;
        --surface: #ffffff;
        --surface-subtle: #f1f5f9;
        --border: #e2e8f0;
        --border-strong: #cbd5e1;
        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-muted: #64748b;
        --text-subtle: #94a3b8;
        --navy: #0f172a;
        --accent: #1e3a8a;
        --accent-blue: #2563eb;
        --accent-sky: #0284c7;
        --success: #047857;
        --success-bg: #ecfdf5;
        --success-border: #a7f3d0;
        --warning: #b45309;
        --warning-bg: #fffbeb;
        --warning-border: #fde68a;
        --danger: #b91c1c;
        --danger-bg: #fef2f2;
        --danger-border: #fecaca;
    }

    * {
        font-family: var(--font-main);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    .stApp {
        background-color: var(--bg-page);
        color: var(--text-primary);
    }

    .block-container {
        max-width: 1480px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* Sidebar Structure */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid var(--border);
        box-shadow: none;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
    }

    .lh-sidebar-header {
        padding-bottom: 1.25rem;
        margin-bottom: 1.25rem;
        border-bottom: 1px solid var(--border);
    }

    .lh-brand-lockup {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }

    .lh-brand-mark {
        width: 32px;
        height: 32px;
        background-color: var(--navy);
        color: #ffffff;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.8rem;
        letter-spacing: 0.05em;
    }

    .lh-brand-text {
        font-size: 0.95rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: var(--text-primary);
        line-height: 1.1;
    }

    .lh-brand-sub {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 0.15rem;
    }

    /* Header Banner */
    .lh-header-card {
        background-color: #ffffff;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        flex-wrap: wrap;
        gap: 1rem;
    }

    .lh-header-eyebrow {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--accent-blue);
        margin-bottom: 0.35rem;
    }

    .lh-header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin-bottom: 0.25rem;
    }

    .lh-header-desc {
        color: var(--text-muted);
        font-size: 0.85rem;
        line-height: 1.45;
        max-width: 680px;
    }

    .lh-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        background-color: var(--surface-subtle);
        border: 1px solid var(--border);
        font-size: 0.72rem;
        font-weight: 600;
        color: var(--text-secondary);
    }

    .lh-status-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: var(--success);
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        transition: border-color 0.15s ease;
    }

    div[data-testid="stMetric"]:hover {
        border-color: var(--border-strong);
    }

    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-size: 1.85rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }

    /* Badges & Tags */
    .lh-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.2rem 0.55rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }

    .lh-badge-high {
        background-color: var(--danger-bg);
        color: var(--danger);
        border: 1px solid var(--danger-border);
    }

    .lh-badge-medium {
        background-color: var(--warning-bg);
        color: var(--warning);
        border: 1px solid var(--warning-border);
    }

    .lh-badge-low {
        background-color: var(--success-bg);
        color: var(--success);
        border: 1px solid var(--success-border);
    }

    .lh-badge-neutral {
        background-color: var(--surface-subtle);
        color: var(--text-secondary);
        border: 1px solid var(--border);
    }

    /* Section Headings */
    .lh-section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.01em;
        margin-bottom: 0.2rem;
    }

    .lh-section-desc {
        color: var(--text-muted);
        font-size: 0.8rem;
        margin-bottom: 1rem;
    }

    /* Dossier Containers */
    .lh-dossier-card {
        background-color: #ffffff;
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1.5rem;
        height: 100%;
    }

    .lh-dossier-header {
        border-bottom: 1px solid var(--border);
        padding-bottom: 1rem;
        margin-bottom: 1.25rem;
    }

    .lh-dossier-id {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        background-color: var(--surface-subtle);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        border: 1px solid var(--border);
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    .lh-dossier-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: var(--text-primary);
        line-height: 1.35;
        margin-bottom: 0.35rem;
    }

    .lh-dossier-org {
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 500;
    }

    .lh-field-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
        margin-bottom: 1rem;
    }

    @media (max-width: 640px) {
        .lh-field-grid {
            grid-template-columns: 1fr;
        }
    }

    .lh-field-box {
        background-color: var(--surface-subtle);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 0.85rem 1rem;
    }

    .lh-field-label {
        font-size: 0.68rem;
        font-weight: 600;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.25rem;
    }

    .lh-field-value {
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text-primary);
        line-height: 1.4;
        word-break: break-word;
    }

    .lh-content-block {
        background-color: var(--surface-subtle);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.1rem 1.25rem;
        color: var(--text-primary);
        font-size: 0.86rem;
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    .lh-callout-action {
        background-color: #f8fafc;
        border-left: 3px solid var(--accent-blue);
        border-top: 1px solid var(--border);
        border-right: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        border-radius: 0 8px 8px 0;
        padding: 1rem 1.15rem;
        font-size: 0.85rem;
        color: var(--text-primary);
        line-height: 1.5;
        margin-bottom: 1rem;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.25rem;
        border-bottom: 1px solid var(--border);
        padding-bottom: 0px;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-muted);
        padding: 0.65rem 0.25rem;
        border-radius: 0;
        border-bottom: 2px solid transparent;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important;
        border-bottom: 2px solid var(--navy) !important;
        font-weight: 700;
    }

    /* Inputs, Buttons, Dataframes */
    div[data-testid="stTextInput"] input,
    div[data-testid="stSelectbox"] > div > div {
        border-radius: 6px !important;
        border-color: var(--border) !important;
        font-size: 0.85rem !important;
    }

    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        border: 1px solid var(--border-strong);
        background-color: #ffffff;
        color: var(--text-primary);
        transition: all 0.15s ease;
    }

    .stButton > button:hover {
        background-color: var(--surface-subtle);
        border-color: var(--text-secondary);
    }

    .stLinkButton > a {
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        background-color: var(--navy) !important;
        color: #ffffff !important;
        border: none !important;
        transition: opacity 0.15s ease;
    }

    .stLinkButton > a:hover {
        opacity: 0.9;
    }

    /* Footer */
    .lh-footer {
        text-align: center;
        color: var(--text-subtle);
        font-size: 0.72rem;
        padding-top: 3rem;
        border-top: 1px solid var(--border);
        margin-top: 3rem;
        line-height: 1.6;
    }

    /* Responsive Adjustments */
    @media (max-width: 900px) {
        .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        .lh-header-title {
            font-size: 1.35rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ================================================================
# Cached Data Loaders
# ================================================================

@st.cache_data(ttl=300)
def get_opportunities():
    return load_opportunities()


@st.cache_data(ttl=300)
def get_activity_log():
    return load_activity_log()


def clean(value, limit=None):
    text = str(value or "").strip()
    if not text:
        return "—"
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def score_value(record):
    try:
        return float(record.get("Score", 0))
    except (TypeError, ValueError):
        return 0.0


def normalized_values(records, field):
    return sorted(
        {
            str(record.get(field, "")).strip()
            for record in records
            if str(record.get(field, "")).strip()
        }
    )


# ================================================================
# Data Loading & Initialization
# ================================================================

try:
    records = get_opportunities()
except Exception as exc:
    st.error("Unable to load opportunities from Google Sheets backend.")
    with st.expander("Technical Details"):
        st.exception(exc)
    st.stop()

metrics = build_dashboard_metrics(records)
quality = build_data_quality_metrics(records)

try:
    activity_log = get_activity_log()
    daily_run_audit = build_daily_run_audit(activity_log)
except Exception:
    activity_log = []
    daily_run_audit = []


opportunity_trend = build_opportunity_trend(records)
priority_distribution = build_priority_distribution(records)
qualification_trend = build_qualification_trend(records)
deadline_distribution = build_deadline_distribution(records)


# ================================================================
# Sidebar Filters
# ================================================================

with st.sidebar:
    st.markdown(
        """
        <div class="lh-sidebar-header">
            <div class="lh-brand-lockup">
                <div class="lh-brand-mark">LH</div>
                <div>
                    <div class="lh-brand-text">LIVEHOOAH</div>
                    <div class="lh-brand-sub">Tender Intelligence</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### Filter Opportunities")

    search = st.text_input(
        "Search records",
        placeholder="Keyword, ID, organization, location...",
        help="Search across title, organization, scope, or location",
    )

    priority_values = normalized_values(records, "Priority")
    priority = st.selectbox(
        "Priority Tier",
        ["All Priorities"] + priority_values,
        index=0,
    )

    status_values = normalized_values(records, "Opportunity_Status")
    status = st.selectbox(
        "Opportunity Status",
        ["All Statuses"] + status_values,
        index=0,
    )

    urgency_filter = st.selectbox(
        "Deadline Urgency",
        [
            "All Deadlines",
            "Active / Upcoming Only",
            "Due Within 7 Days",
            "Due Within 30 Days",
            "Expired Only",
        ],
        index=0,
    )

    min_score = st.slider(
        "Minimum Match Score",
        min_value=0.0,
        max_value=1.0,
        value=0.0,
        step=0.05,
        help="Filter opportunities at or above this match score threshold",
    )

    st.divider()

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_s2:
        if st.button("Reset", use_container_width=True):
            st.rerun()

    st.markdown(
        f"""
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem; margin-top: 1rem; font-size: 0.72rem; color: #64748b;">
            <div style="font-weight: 600; color: #0f172a; margin-bottom: 0.25rem;">Sync Information</div>
            <div>Source: Google Sheets</div>
            <div>Indexed Opportunities: {len(records)}</div>
            <div>Connection: Active (Read-only)</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================
# Filter Processing
# ================================================================

filtered_records = filter_opportunities(
    records,
    priority=None if priority == "All Priorities" else priority,
    status=None if status == "All Statuses" else status,
    search=search or None,
)

if min_score > 0.0:
    filtered_records = [
        r for r in filtered_records
        if score_value(r) >= min_score
    ]

today_date = date.today()
if urgency_filter == "Active / Upcoming Only":
    filtered_records = [
        r for r in filtered_records
        if get_deadline_status(r.get("Deadline"), today=today_date)["status"] in ("UPCOMING", "TODAY")
    ]
elif urgency_filter == "Due Within 7 Days":
    filtered_records = [
        r for r in filtered_records
        if get_deadline_status(r.get("Deadline"), today=today_date)["status"] == "TODAY" or
        (get_deadline_status(r.get("Deadline"), today=today_date)["status"] == "UPCOMING" and
         get_deadline_status(r.get("Deadline"), today=today_date)["days"] is not None and
         get_deadline_status(r.get("Deadline"), today=today_date)["days"] <= 7)
    ]
elif urgency_filter == "Due Within 30 Days":
    filtered_records = [
        r for r in filtered_records
        if get_deadline_status(r.get("Deadline"), today=today_date)["status"] == "TODAY" or
        (get_deadline_status(r.get("Deadline"), today=today_date)["status"] == "UPCOMING" and
         get_deadline_status(r.get("Deadline"), today=today_date)["days"] is not None and
         get_deadline_status(r.get("Deadline"), today=today_date)["days"] <= 30)
    ]
elif urgency_filter == "Expired Only":
    filtered_records = [
        r for r in filtered_records
        if get_deadline_status(r.get("Deadline"), today=today_date)["status"] == "EXPIRED"
    ]

filtered_records = sort_opportunities_by_deadline(filtered_records)


# ================================================================
# Header
# ================================================================

st.markdown(
    f"""
    <div class="lh-header-card">
        <div>
            <div class="lh-header-eyebrow">Structural Engineering Pipeline</div>
            <div class="lh-header-title">Tender Intelligence Command Center</div>
            <div class="lh-header-desc">
                Automated discovery, structural qualification scoring, extraction diagnostics, and pursuit context.
            </div>
        </div>
        <div style="text-align: right;">
            <div class="lh-status-pill">
                <span class="lh-status-dot"></span> Pipeline Connected
            </div>
            <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 0.45rem;">
                Last sync: {datetime.now():%d %b %Y, %H:%M}
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ================================================================
# Top-Level KPI Summary
# ================================================================

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

qual_ratio = (
    round((metrics["qualified"] / metrics["total"] * 100), 1)
    if metrics["total"] > 0
    else 0.0
)

kpi1.metric(
    label="Total Opportunities",
    value=str(metrics["total"]),
    help="Total tenders discovered and indexed across all sources",
)

kpi2.metric(
    label="Qualified Pursuits",
    value=str(metrics["qualified"]),
    delta=f"{qual_ratio}% qualification rate",
    delta_color="normal",
    help="Tenders matching LiveHooah engineering qualification criteria",
)

kpi3.metric(
    label="High Priority",
    value=str(metrics["high_priority"]),
    help="High-value structural engineering opportunities",
)

kpi4.metric(
    label="Upcoming Deadlines",
    value=str(metrics["upcoming_deadlines"]),
    help="Opportunities with valid submission deadlines on or after today",
)

st.write("")


# ================================================================
# Main Navigation Tabs
# ================================================================

tab_explorer, tab_analytics, tab_audit, tab_health = st.tabs(
    [
        "Opportunity Explorer & Dossier",
        "Pipeline Analytics",
        "Daily Run Audit",
        "Extraction Diagnostics",
    ]
)


# ================================================================
# TAB 1: Opportunity Explorer & Dossier
# ================================================================

with tab_explorer:
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.85rem;">
            <div>
                <div class="lh-section-title">Opportunity Directory</div>
                <div class="lh-section-desc">Qualified tenders sorted by nearest valid deadline and relevance score.</div>
            </div>
            <div>
                <span class="lh-badge lh-badge-neutral">
                    {len(filtered_records)} of {len(records)} displayed
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not filtered_records:
        st.info("No opportunities match the current filter selection.")
    else:
        table_rows = []
        for rec in filtered_records:
            deadline_info = get_deadline_status(rec.get("Deadline"))
            table_rows.append(
                {
                    "ID": clean(rec.get("Opportunity_ID")),
                    "Priority": clean(rec.get("Priority")),
                    "Score": score_value(rec),
                    "Title": clean(rec.get("Title"), 85),
                    "Issuing Authority": clean(rec.get("Organization"), 40),
                    "Location": clean(rec.get("Location"), 30),
                    "Deadline": clean(rec.get("Deadline")),
                    "Urgency": deadline_info["label"],
                    "Status": clean(rec.get("Opportunity_Status")),
                    "Source": rec.get("Source_Link", ""),
                }
            )

        df_display = pd.DataFrame(table_rows)

        st.dataframe(
            df_display,
            width="stretch",
            hide_index=True,
            height=340,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small"),
                "Priority": st.column_config.TextColumn("Priority", width="small"),
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                    width="small",
                ),
                "Title": st.column_config.TextColumn("Title", width="large"),
                "Issuing Authority": st.column_config.TextColumn("Organization", width="medium"),
                "Location": st.column_config.TextColumn("Location", width="small"),
                "Deadline": st.column_config.TextColumn("Deadline", width="small"),
                "Urgency": st.column_config.TextColumn("Urgency", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "Source": st.column_config.LinkColumn("Source", display_text="Open", width="small"),
            },
        )

        csv_data = df_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Export Filtered Results (CSV)",
            data=csv_data,
            file_name=f"livehooah_opportunities_{datetime.now():%Y%m%d_%H%M}.csv",
            mime="text/csv",
        )

        st.divider()

        # Opportunity Dossier Detail
        st.markdown(
            """
            <div class="lh-section-title">Tender Intelligence Dossier</div>
            <div class="lh-section-desc">Select an opportunity below to view comprehensive structural scope and qualification rationale.</div>
            """,
            unsafe_allow_html=True,
        )

        labels = {}
        for idx, record in enumerate(filtered_records):
            prio_tag = str(record.get("Priority", "MED")).upper()
            lbl = f"[{prio_tag}] {clean(record.get('Opportunity_ID'))} - {clean(record.get('Title'), 75)} ({clean(record.get('Organization'), 35)})"
            if lbl in labels:
                lbl = f"{lbl} #{idx + 1}"
            labels[lbl] = record

        selected_label = st.selectbox(
            "Select Record to Inspect",
            options=list(labels.keys()),
            help="Choose an opportunity to view its detailed analysis dossier",
        )

        selected = labels[selected_label]
        dl_status = get_deadline_status(selected.get("Deadline"))
        score = score_value(selected)
        prio_str = str(selected.get("Priority", "MEDIUM")).upper()

        badge_class = (
            "lh-badge-high"
            if prio_str == "HIGH"
            else ("lh-badge-medium" if prio_str == "MEDIUM" else "lh-badge-low")
        )

        dossier_col_l, dossier_col_r = st.columns([1.1, 1.4], gap="large")

        with dossier_col_l:
            st.markdown(
                f"""
                <div class="lh-dossier-card">
                    <div class="lh-dossier-header">
                        <div style="display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem;">
                            <span class="lh-dossier-id">{clean(selected.get('Opportunity_ID'))}</span>
                            <span class="lh-badge {badge_class}">{prio_str} Priority</span>
                        </div>
                        <div class="lh-dossier-title">{clean(selected.get('Title'))}</div>
                        <div class="lh-dossier-org">{clean(selected.get('Organization'))}</div>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
                <div class="lh-field-grid">
                    <div class="lh-field-box">
                        <div class="lh-field-label">Match Score</div>
                        <div class="lh-field-value">{score:.2f} / 1.00</div>
                    </div>
                    <div class="lh-field-box">
                        <div class="lh-field-label">Deadline</div>
                        <div class="lh-field-value">{clean(selected.get('Deadline'))}<br><span style="font-size: 0.72rem; color: var(--text-muted); font-weight: 500;">{dl_status['label']}</span></div>
                    </div>
                    <div class="lh-field-box">
                        <div class="lh-field-label">Location</div>
                        <div class="lh-field-value">{clean(selected.get('Location'))}</div>
                    </div>
                    <div class="lh-field-box">
                        <div class="lh-field-label">Tender Type</div>
                        <div class="lh-field-value">{clean(selected.get('Type'))}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            source_url = str(selected.get("Source_Link", "")).strip()
            if source_url:
                st.link_button(
                    "Open Tender Source Link",
                    source_url,
                    use_container_width=True,
                )

            st.markdown("</div>", unsafe_allow_html=True)

        with dossier_col_r:
            st.markdown(
                """
                <div class="lh-dossier-card">
                    <div class="lh-section-title">Qualification Rationale & Scope</div>
                    <div class="lh-section-desc">Automated structural alignment assessment and pursuit recommendations.</div>
                """,
                unsafe_allow_html=True,
            )

            reasoning_val = clean(selected.get("Qualification_Reasoning"))
            st.markdown(
                f"""
                <div class="lh-field-label">Qualification Reasoning</div>
                <div class="lh-content-block">
                    {reasoning_val}
                </div>
                """,
                unsafe_allow_html=True,
            )

            rec_action = str(selected.get("Recommended_Action", "")).strip()
            if rec_action:
                st.markdown(
                    f"""
                    <div class="lh-field-label">Recommended Action</div>
                    <div class="lh-callout-action">
                        {rec_action}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            summary_val = str(selected.get("Summary", "")).strip()
            if summary_val:
                st.markdown(
                    f"""
                    <div class="lh-field-label">Scope Summary</div>
                    <div class="lh-content-block">
                        {summary_val}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            st.markdown(
                f"""
                <div class="lh-field-grid">
                    <div class="lh-field-box">
                        <div class="lh-field-label">Opportunity Status</div>
                        <div class="lh-field-value">{clean(selected.get('Opportunity_Status'))}</div>
                    </div>
                    <div class="lh-field-box">
                        <div class="lh-field-label">Contact Status</div>
                        <div class="lh-field-value">{clean(selected.get('Contact_Status'))}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("</div>", unsafe_allow_html=True)


# ================================================================
# TAB 2: Pipeline Analytics
# ================================================================

with tab_analytics:
    st.markdown(
        """
        <div class="lh-section-title">Pipeline Analytics</div>
        <div class="lh-section-desc">Discovery volume, priority distribution, qualification yields, and deadline horizons.</div>
        """,
        unsafe_allow_html=True,
    )

    an1, an2 = st.columns(2)

    with an1:
        st.markdown("##### Opportunities Discovered Over Time")
        if opportunity_trend:
            df_trend = pd.DataFrame(opportunity_trend).set_index("Date")
            st.line_chart(
                df_trend["Opportunities"],
                use_container_width=True,
                color="#2563eb",
            )
        else:
            st.info("No time-series discovery data available.")

    with an2:
        st.markdown("##### Priority Distribution")
        if priority_distribution:
            df_prio = pd.DataFrame(priority_distribution).set_index("Priority")
            st.bar_chart(
                df_prio["Opportunities"],
                use_container_width=True,
                color="#0f172a",
            )
        else:
            st.info("No priority distribution data available.")

    st.divider()

    an3, an4 = st.columns(2)

    with an3:
        st.markdown("##### Qualification Volume (Discovered vs Qualified)")
        if qualification_trend:
            df_qual = pd.DataFrame(qualification_trend).set_index("Date")
            st.line_chart(
                df_qual[["Opportunities", "Qualified"]],
                use_container_width=True,
                color=["#94a3b8", "#047857"],
            )
        else:
            st.info("No qualification trend data available.")

    with an4:
        st.markdown("##### Deadline Status (Upcoming vs Expired)")
        if deadline_distribution:
            df_dead = pd.DataFrame(deadline_distribution).set_index("Status")
            st.bar_chart(
                df_dead["Opportunities"],
                use_container_width=True,
                color="#475569",
            )
        else:
            st.info("No deadline distribution data available.")


# ================================================================
# TAB 3: Daily Run Audit
# ================================================================

with tab_audit:
    st.markdown(
        """
        <div class="lh-section-title">Daily Run Audit Log</div>
        <div class="lh-section-desc">System execution history, yield outcomes, deduplication metrics, and non-save reason codes.</div>
        """,
        unsafe_allow_html=True,
    )

    if not daily_run_audit:
        st.info("No daily run audit records found in Activity_Log.")
    else:
        df_audit = pd.DataFrame(daily_run_audit)

        aud1, aud2, aud3, aud4 = st.columns(4)
        aud1.metric("Total Execution Runs", len(df_audit))
        aud2.metric("Saved Opportunities", int(df_audit["Saved"].sum()) if "Saved" in df_audit else 0)
        aud3.metric("Duplicates Filtered", int(df_audit["Duplicates"].sum()) if "Duplicates" in df_audit else 0)
        aud4.metric("Unqualified / Failed", int(df_audit["Failed"].sum()) if "Failed" in df_audit else 0)

        st.write("")

        st.dataframe(
            df_audit,
            width="stretch",
            hide_index=True,
            column_config={
                "Run Date": st.column_config.TextColumn("Run Date", width="small"),
                "Reason": st.column_config.TextColumn("Run Outcome & Notes", width="large"),
                "Qualified": st.column_config.NumberColumn("Qualified", width="small"),
                "Saved": st.column_config.NumberColumn("Saved", width="small"),
                "Duplicates": st.column_config.NumberColumn("Duplicates", width="small"),
                "Failed": st.column_config.NumberColumn("Failed", width="small"),
            },
        )


# ================================================================
# TAB 4: Extraction Diagnostics
# ================================================================

with tab_health:
    st.markdown(
        """
        <div class="lh-section-title">Data Quality & Extraction Diagnostics</div>
        <div class="lh-section-desc">Automated metadata validation checks across all indexed opportunities.</div>
        """,
        unsafe_allow_html=True,
    )

    h1, h2, h3, h4 = st.columns(4)

    h1.metric(
        label="Missing Deadlines",
        value=quality["missing_deadlines"],
        help="Records without any deadline date specified",
    )

    h2.metric(
        label="Invalid Deadlines",
        value=quality["invalid_deadlines"],
        help="Records with unparseable non-ISO deadline format",
    )

    h3.metric(
        label="Suspicious Locations",
        value=quality["suspicious_locations"],
        help="Records where location appears to contain raw URLs or generic boilerplate text",
    )

    h4.metric(
        label="Missing Source Links",
        value=quality["missing_source_links"],
        help="Records missing canonical tender source links",
    )

    st.markdown(
        """
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1.25rem 1.5rem; margin-top: 1.5rem;">
            <div style="font-weight: 600; color: #0f172a; font-size: 0.9rem; margin-bottom: 0.35rem;">
                Diagnostics Governance Policy
            </div>
            <div style="color: #64748b; font-size: 0.84rem; line-height: 1.55;">
                These diagnostics identify potential metadata extraction anomalies for auditing purposes.
                The dashboard runs in strict read-only mode and does not alter stored records.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ================================================================
# Application Footer
# ================================================================

st.markdown(
    f"""
    <div class="lh-footer">
        LIVEHOOAH Tender Intelligence System &middot; Structural Engineering Practice<br>
        Autonomous Pipeline &middot; Google Sheets Integration &middot; Refreshed: {datetime.now():%d %b %Y, %H:%M:%S}
    </div>
    """,
    unsafe_allow_html=True,
)
