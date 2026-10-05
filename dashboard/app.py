from datetime import datetime
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
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ================================================================
# Visual theme
# ================================================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            linear-gradient(
                180deg,
                #f7f9fc 0%,
                #f4f7fa 100%
            );
    }

    .block-container {
        max-width: 1480px;
        padding-top: 1.5rem;
        padding-bottom: 3.5rem;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5eaf0;
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    .lh-brand {
        margin-bottom: 1.5rem;
    }

    .lh-brand-row {
        display: flex;
        align-items: center;
        gap: .7rem;
    }

    .lh-logo {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        background:
            linear-gradient(
                135deg,
                #10243d,
                #176b67
            );
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: .78rem;
        font-weight: 800;
        box-shadow:
            0 5px 15px
            rgba(16, 36, 61, .18);
    }

    .lh-name {
        color: #122033;
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: .06em;
    }

    .lh-brand-copy {
        color: #8490a0;
        font-size: .73rem;
        margin-top: .35rem;
        margin-left: 2.95rem;
    }

    .lh-eyebrow {
        color: #16806d;
        font-size: .69rem;
        font-weight: 800;
        letter-spacing: .14em;
        text-transform: uppercase;
        margin-bottom: .35rem;
    }

    .lh-title {
        color: #132238;
        font-size: 2rem;
        line-height: 1.15;
        font-weight: 780;
        letter-spacing: -.025em;
    }

    .lh-subtitle {
        color: #718096;
        font-size: .91rem;
        margin-top: .4rem;
        margin-bottom: .25rem;
    }

    .lh-live {
        display: inline-flex;
        align-items: center;
        gap: .4rem;
        color: #587082;
        background: #eef5f3;
        border: 1px solid #dcebe6;
        padding: .3rem .6rem;
        border-radius: 999px;
        font-size: .68rem;
        font-weight: 650;
        margin-top: .7rem;
    }

    .lh-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #20a47c;
        display: inline-block;
    }

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e4eaf0;
        border-radius: 14px;
        padding: 1rem 1.1rem;
        box-shadow:
            0 5px 16px
            rgba(22, 34, 51, .04);
    }

    div[data-testid="stMetricLabel"] {
        color: #788596;
        font-size: .73rem;
        font-weight: 700;
        letter-spacing: .02em;
    }

    div[data-testid="stMetricValue"] {
        color: #14243a;
        font-size: 1.8rem;
        font-weight: 780;
    }

    .lh-section {
        margin-top: 1.8rem;
        margin-bottom: .8rem;
    }

    .lh-section-title {
        color: #15263b;
        font-size: 1.18rem;
        font-weight: 760;
        letter-spacing: -.01em;
    }

    .lh-section-copy {
        color: #7b8796;
        font-size: .8rem;
        margin-top: .18rem;
    }

    .lh-count {
        color: #657386;
        background: #eef2f6;
        border-radius: 999px;
        padding: .28rem .58rem;
        font-size: .68rem;
        font-weight: 700;
    }

    div[data-testid="stDataFrame"] {
        background: white;
        border: 1px solid #e3e9ef;
        border-radius: 13px;
        overflow: hidden;
        box-shadow:
            0 4px 14px
            rgba(20, 35, 55, .035);
    }

    div[data-testid="stSelectbox"] > div > div {
        border-radius: 9px;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 9px;
    }

    .stButton > button,
    .stLinkButton > a {
        border-radius: 9px;
        font-weight: 650;
    }

    div[data-testid="stExpander"] {
        background: white;
        border: 1px solid #e3e9ef;
        border-radius: 12px;
    }

    .lh-detail-card {
        background: #ffffff;
        border: 1px solid #e3e9ef;
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        margin-bottom: .7rem;
        box-shadow:
            0 4px 14px
            rgba(20, 35, 55, .03);
    }

    .lh-detail-label {
        color: #8995a5;
        font-size: .65rem;
        font-weight: 750;
        letter-spacing: .07em;
        text-transform: uppercase;
        margin-bottom: .2rem;
    }

    .lh-detail-value {
        color: #17283e;
        font-size: .87rem;
        font-weight: 620;
        line-height: 1.45;
    }

    .lh-quality-note {
        background: #f9fbfc;
        border: 1px solid #e4eaf0;
        border-radius: 12px;
        padding: .8rem 1rem;
        color: #778597;
        font-size: .75rem;
        line-height: 1.45;
        margin-top: .6rem;
    }

    .lh-footer {
        color: #98a3b0;
        font-size: .68rem;
        text-align: center;
        margin-top: 2.4rem;
    }

    hr {
        border-color: #e9edf2 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
        return float(
            record.get("Score", 0)
        )
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
# Data
# ================================================================

try:
    records = get_opportunities()
except Exception as exc:
    st.error(
        "Unable to load opportunities from Google Sheets."
    )

    with st.expander("Technical details"):
        st.exception(exc)

    st.stop()


metrics = build_dashboard_metrics(records)
quality = build_data_quality_metrics(records)

try:
    activity_log = get_activity_log()
    daily_run_audit = build_daily_run_audit(
        activity_log
    )
except Exception as exc:
    activity_log = []
    daily_run_audit = []
    st.warning(
        "Unable to load daily run audit from Google Sheets."
    )

    with st.expander("Daily run audit technical details"):
        st.exception(exc)


# ================================================================
# Analytics
# ================================================================

opportunity_trend = build_opportunity_trend(records)
priority_distribution = build_priority_distribution(records)
qualification_trend = build_qualification_trend(records)
deadline_distribution = build_deadline_distribution(records)


# ================================================================
# Sidebar
# ================================================================

with st.sidebar:
    st.markdown(
        """
        <div class="lh-brand">
            <div class="lh-brand-row">
                <div class="lh-logo">LH</div>
                <div class="lh-name">LIVEHOOAH</div>
            </div>
            <div class="lh-brand-copy">
                Tender Intelligence
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("##### Find opportunities")

    search = st.text_input(
        "Search opportunities",
        placeholder="Title, organization, location...",
    )

    priority_values = normalized_values(
        records,
        "Priority",
    )

    priority = st.selectbox(
        "Priority",
        ["All"] + priority_values,
    )

    status_values = normalized_values(
        records,
        "Opportunity_Status",
    )

    status = st.selectbox(
        "Opportunity status",
        ["All"] + status_values,
    )

    st.divider()

    st.caption(
        f"{len(records)} opportunities indexed"
    )

    if st.button(
        "Refresh intelligence",
        width="stretch",
    ):
        st.cache_data.clear()
        st.rerun()

    st.caption(
        "Read-only workspace · Google Sheets"
    )


# ================================================================
# Filters
# ================================================================

filtered_records = filter_opportunities(
    records,
    priority=(
        None
        if priority == "All"
        else priority
    ),
    status=(
        None
        if status == "All"
        else status
    ),
    search=search or None,
)

filtered_records = sort_opportunities_by_deadline(
    filtered_records
)


# ================================================================
# Header
# ================================================================

header_left, header_right = st.columns(
    [4, 1]
)

with header_left:
    st.markdown(
        """
        <div class="lh-eyebrow">
            Opportunity Intelligence
        </div>
        <div class="lh-title">
            Tender Intelligence Command Center
        </div>
        <div class="lh-subtitle">
            Structural engineering opportunities,
            qualification signals and pursuit context.
        </div>
        <div class="lh-live">
            <span class="lh-dot"></span>
            Intelligence connected
        </div>
        """,
        unsafe_allow_html=True,
    )

with header_right:
    st.caption("LAST REFRESH")
    st.markdown(
        f"**{datetime.now():%d %b %Y}**"
    )
    st.caption(
        f"{datetime.now():%H:%M}"
    )


# ================================================================
# KPI cards
# ================================================================

st.write("")

kpi_columns = st.columns(4)

kpi_columns[0].metric(
    "TOTAL OPPORTUNITIES",
    metrics["total"],
)

kpi_columns[1].metric(
    "QUALIFIED",
    metrics["qualified"],
)

kpi_columns[2].metric(
    "HIGH PRIORITY",
    metrics["high_priority"],
)

kpi_columns[3].metric(
    "UPCOMING DEADLINES",
    metrics["upcoming_deadlines"],
)


# ================================================================
# Daily Run Audit
# ================================================================

st.markdown(
    """
    <div class="lh-section">
        <div class="lh-section-title">
            Daily Run Audit
        </div>
        <div class="lh-section-copy">
            Scheduler outcomes, including the reason when no
            opportunity was saved.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not daily_run_audit:
    st.info(
        "No daily run audit records found."
    )
else:
    audit_table = pd.DataFrame(
        daily_run_audit
    )

    st.dataframe(
        audit_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Run Date": st.column_config.TextColumn(
                "Run Date",
                width="small",
            ),
            "Reason": st.column_config.TextColumn(
                "Reason",
                width="large",
            ),
            "Qualified": st.column_config.NumberColumn(
                "Qualified",
                width="small",
            ),
            "Saved": st.column_config.NumberColumn(
                "Saved",
                width="small",
            ),
            "Duplicates": st.column_config.NumberColumn(
                "Duplicates",
                width="small",
            ),
            "Failed": st.column_config.NumberColumn(
                "Failed",
                width="small",
            ),
        },
    )


# ================================================================
# Analytics
# ================================================================

st.markdown(
    """
    <div class="lh-section">
        <div class="lh-section-title">
            Analytics
        </div>
        <div class="lh-section-copy">
            Opportunity trends, priority mix, qualification performance,
            and deadline status.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

analytics_col_1, analytics_col_2 = st.columns(2)

with analytics_col_1:
    st.markdown("#### Opportunity Trend")
    if opportunity_trend:
        opportunity_trend_table = pd.DataFrame(
            opportunity_trend
        ).set_index("Date")
        st.line_chart(
            opportunity_trend_table["Opportunities"],
            width="stretch",
        )
    else:
        st.info("No opportunity trend data available.")

with analytics_col_2:
    st.markdown("#### Priority Distribution")
    if priority_distribution:
        priority_table = pd.DataFrame(
            priority_distribution
        ).set_index("Priority")
        st.bar_chart(
            priority_table["Opportunities"],
            width="stretch",
        )
    else:
        st.info("No priority distribution data available.")

analytics_col_3, analytics_col_4 = st.columns(2)

with analytics_col_3:
    st.markdown("#### Qualification Trend")
    if qualification_trend:
        qualification_table = pd.DataFrame(
            qualification_trend
        ).set_index("Date")
        st.line_chart(
            qualification_table[
                ["Opportunities", "Qualified"]
            ],
            width="stretch",
        )
    else:
        st.info("No qualification trend data available.")

with analytics_col_4:
    st.markdown("#### Deadline Distribution")
    if deadline_distribution:
        deadline_table = pd.DataFrame(
            deadline_distribution
        ).set_index("Status")
        st.bar_chart(
            deadline_table["Opportunities"],
            width="stretch",
        )
    else:
        st.info("No deadline distribution data available.")


# ================================================================
# Opportunity Explorer
# ================================================================

st.markdown(
    f"""
    <div class="lh-section">
        <div class="lh-section-title">
            Opportunity Explorer
        </div>
        <div class="lh-section-copy">
            Qualified opportunities ordered by nearest valid deadline.
            &nbsp;&nbsp;
            <span class="lh-count">
                {len(filtered_records)} shown
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if not filtered_records:
    st.info(
        "No opportunities match the selected filters."
    )

else:
    table_rows = []

    for record in filtered_records:
        deadline = get_deadline_status(
            record.get("Deadline")
        )

        table_rows.append(
            {
                "ID": clean(
                    record.get("Opportunity_ID"),
                    18,
                ),
                "Priority": clean(
                    record.get("Priority")
                ),
                "Score": score_value(record),
                "Opportunity": clean(
                    record.get("Title"),
                    80,
                ),
                "Organization": clean(
                    record.get("Organization"),
                    45,
                ),
                "Location": clean(
                    record.get("Location"),
                    38,
                ),
                "Deadline": clean(
                    record.get("Deadline")
                ),
                "Urgency": deadline["label"],
                "Tender": record.get(
                    "Source_Link",
                    "",
                ),
            }
        )

    table = pd.DataFrame(
        table_rows
    )

    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        height=420,
        column_config={
            "ID": st.column_config.TextColumn(
                "ID",
                width="small",
            ),
            "Priority": st.column_config.TextColumn(
                "Priority",
                width="small",
            ),
            "Score": st.column_config.ProgressColumn(
                "Score",
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
                width="small",
            ),
            "Opportunity": st.column_config.TextColumn(
                "Opportunity",
                width="large",
            ),
            "Organization": st.column_config.TextColumn(
                "Organization",
                width="medium",
            ),
            "Location": st.column_config.TextColumn(
                "Location",
                width="medium",
            ),
            "Deadline": st.column_config.TextColumn(
                "Deadline",
                width="small",
            ),
            "Urgency": st.column_config.TextColumn(
                "Urgency",
                width="small",
            ),
            "Tender": st.column_config.LinkColumn(
                "Source",
                display_text="Open ↗",
                width="small",
            ),
        },
    )


# ================================================================
# Intelligence detail
# ================================================================

if filtered_records:
    st.markdown(
        """
        <div class="lh-section">
            <div class="lh-section-title">
                Tender Intelligence
            </div>
            <div class="lh-section-copy">
                Select an opportunity to review its
                qualification and pursuit context.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels = {}

    for index, record in enumerate(
        filtered_records
    ):
        label = (
            f"{clean(record.get('Opportunity_ID'))} · "
            f"{clean(record.get('Title'), 80)}"
        )

        if label in labels:
            label = f"{label} · {index + 1}"

        labels[label] = record

    selected_label = st.selectbox(
        "Select tender",
        list(labels.keys()),
        label_visibility="collapsed",
    )

    selected = labels[selected_label]

    deadline = get_deadline_status(
        selected.get("Deadline")
    )

    left, right = st.columns(
        [1, 1.35],
        gap="large",
    )

    with left:
        st.markdown(
            "##### Opportunity overview"
        )

        st.markdown(
            f"**{clean(selected.get('Title'))}**"
        )

        st.caption(
            clean(
                selected.get("Organization")
            )
        )

        overview_a, overview_b = st.columns(2)

        overview_a.metric(
            "Priority",
            clean(
                selected.get("Priority")
            ),
        )

        overview_b.metric(
            "Score",
            f"{score_value(selected):.2f}",
        )

        st.markdown(
            f"**Deadline**  \n"
            f"{clean(selected.get('Deadline'))} "
            f"· {deadline['label']}"
        )

        st.markdown(
            f"**Location**  \n"
            f"{clean(selected.get('Location'))}"
        )

        st.markdown(
            f"**Tender type**  \n"
            f"{clean(selected.get('Type'))}"
        )

        source_link = str(
            selected.get(
                "Source_Link",
                "",
            )
        ).strip()

        if source_link:
            st.link_button(
                "Open tender source ↗",
                source_link,
            )

    with right:
        st.markdown(
            "##### Qualification context"
        )

        reasoning = clean(
            selected.get(
                "Qualification_Reasoning"
            )
        )

        st.write(reasoning)

        recommended = str(
            selected.get(
                "Recommended_Action",
                "",
            )
        ).strip()

        if recommended:
            st.markdown(
                "**Recommended action**"
            )
            st.write(recommended)

        summary = str(
            selected.get(
                "Summary",
                "",
            )
        ).strip()

        if summary:
            st.markdown("**Summary**")
            st.write(summary)

        status_left, status_right = st.columns(2)

        status_left.markdown(
            "**Opportunity status**"
        )
        status_left.write(
            clean(
                selected.get(
                    "Opportunity_Status"
                )
            )
        )

        status_right.markdown(
            "**Contact status**"
        )
        status_right.write(
            clean(
                selected.get(
                    "Contact_Status"
                )
            )
        )


# ================================================================
# Intelligence health
# ================================================================

st.markdown(
    """
    <div class="lh-section">
        <div class="lh-section-title">
            Intelligence Health
        </div>
        <div class="lh-section-copy">
            Metadata diagnostics for improving extraction quality.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander(
    "View data quality diagnostics"
):
    quality_columns = st.columns(4)

    quality_columns[0].metric(
        "Missing deadlines",
        quality["missing_deadlines"],
    )

    quality_columns[1].metric(
        "Invalid deadlines",
        quality["invalid_deadlines"],
    )

    quality_columns[2].metric(
        "Suspicious locations",
        quality["suspicious_locations"],
    )

    quality_columns[3].metric(
        "Missing source links",
        quality["missing_source_links"],
    )

    st.markdown(
        """
        <div class="lh-quality-note">
            Diagnostics surface questionable metadata only.
            The dashboard does not silently alter stored tender data.
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    f"""
    <div class="lh-footer">
        LIVEHOOAH Tender Intelligence System
        &nbsp;·&nbsp;
        Decision workspace
        &nbsp;·&nbsp;
        {datetime.now():%d %b %Y, %H:%M}
    </div>
    """,
    unsafe_allow_html=True,
)
