from dashboard.dashboard_data import (
    build_dashboard_metrics,
)


def test_build_dashboard_metrics_counts_opportunities():
    records = [
        {
            "Opportunity_ID": "OPP-000001",
            "Title": "Structural Consultancy Services",
            "Priority": "HIGH",
            "Qualified": True,
            "Deadline": "2026-10-21",
        },
        {
            "Opportunity_ID": "OPP-000002",
            "Title": "Structural Audit Services",
            "Priority": "MEDIUM",
            "Qualified": True,
            "Deadline": "2026-11-15",
        },
        {
            "Opportunity_ID": "OPP-000003",
            "Title": "Old Opportunity",
            "Priority": "LOW",
            "Qualified": False,
            "Deadline": "2026-09-01",
        },
    ]

    metrics = build_dashboard_metrics(
        records,
        today="2026-10-02",
    )

    assert metrics == {
        "total": 3,
        "qualified": 2,
        "high_priority": 1,
        "upcoming_deadlines": 2,
    }


def test_build_dashboard_metrics_normalizes_sheet_boolean_values():
    records = [
        {
            "Opportunity_ID": "OPP-000001",
            "Priority": "HIGH",
            "Qualified": "TRUE",
            "Deadline": "2026-10-21",
        },
        {
            "Opportunity_ID": "OPP-000002",
            "Priority": "MEDIUM",
            "Qualified": "FALSE",
            "Deadline": "2026-10-01",
        },
        {
            "Opportunity_ID": "OPP-000003",
            "Priority": "LOW",
            "Qualified": True,
            "Deadline": "",
        },
    ]

    metrics = build_dashboard_metrics(
        records,
        today="2026-10-02",
    )

    assert metrics["qualified"] == 2
    assert metrics["upcoming_deadlines"] == 1


def test_filter_opportunities_by_priority_status_and_search():
    from dashboard.dashboard_data import filter_opportunities

    records = [
        {
            "Opportunity_ID": "OPP-000001",
            "Title": "Structural Consultancy for Entry Gate",
            "Organization": "YEIDA",
            "Location": "Greater Noida",
            "Priority": "HIGH",
            "Opportunity_Status": "NEW",
        },
        {
            "Opportunity_ID": "OPP-000002",
            "Title": "Structural Audit of Hospital",
            "Organization": "AIIMS",
            "Location": "New Delhi",
            "Priority": "HIGH",
            "Opportunity_Status": "REVIEWING",
        },
        {
            "Opportunity_ID": "OPP-000003",
            "Title": "Industrial Building Design",
            "Organization": "Development Authority",
            "Location": "Lucknow",
            "Priority": "MEDIUM",
            "Opportunity_Status": "NEW",
        },
    ]

    filtered = filter_opportunities(
        records,
        priority="HIGH",
        status="NEW",
        search="yeida",
    )

    assert len(filtered) == 1
    assert filtered[0]["Opportunity_ID"] == "OPP-000001"


def test_sort_opportunities_by_deadline_puts_nearest_valid_first():
    from dashboard.dashboard_data import sort_opportunities_by_deadline

    records = [
        {
            "Opportunity_ID": "OPP-000001",
            "Deadline": "2026-11-15",
        },
        {
            "Opportunity_ID": "OPP-000002",
            "Deadline": "",
        },
        {
            "Opportunity_ID": "OPP-000003",
            "Deadline": "2026-10-21",
        },
        {
            "Opportunity_ID": "OPP-000004",
            "Deadline": "not-a-date",
        },
    ]

    sorted_records = sort_opportunities_by_deadline(records)

    assert [
        record["Opportunity_ID"]
        for record in sorted_records
    ] == [
        "OPP-000003",
        "OPP-000001",
        "OPP-000002",
        "OPP-000004",
    ]


def test_load_opportunities_uses_existing_sheets_client_contract():
    from unittest.mock import Mock

    from config.constants import OPPORTUNITIES_SHEET
    from dashboard.dashboard_data import load_opportunities

    client = Mock()

    client.read_records.return_value = [
        {
            "Opportunity_ID": "OPP-000014",
            "Title": "Structural Consultancy Services",
            "Location": "Gautam Budh Nagar District, Uttar Pradesh",
            "Priority": "HIGH",
        }
    ]

    records = load_opportunities(
        sheets_client=client,
    )

    client.read_records.assert_called_once_with(
        OPPORTUNITIES_SHEET
    )

    assert len(records) == 1
    assert (
        records[0]["Opportunity_ID"]
        == "OPP-000014"
    )
    assert (
        records[0]["Location"]
        == "Gautam Budh Nagar District, Uttar Pradesh"
    )


def test_build_data_quality_metrics_identifies_suspicious_records():
    from dashboard.dashboard_data import build_data_quality_metrics

    records = [
        {
            "Opportunity_ID": "OPP-000001",
            "Location": "Gautam Budh Nagar District, Uttar Pradesh",
            "Deadline": "2026-10-21",
            "Source_Link": "https://example.com/tender/1",
        },
        {
            "Opportunity_ID": "OPP-000002",
            "Location": "www.pwd.py.gov.in",
            "Deadline": "",
            "Source_Link": "https://example.com/tender/2",
        },
        {
            "Opportunity_ID": "OPP-000003",
            "Location": "The proposal may be submitted",
            "Deadline": "not-a-date",
            "Source_Link": "",
        },
    ]

    metrics = build_data_quality_metrics(records)

    assert metrics == {
        "missing_deadlines": 1,
        "invalid_deadlines": 1,
        "suspicious_locations": 2,
        "missing_source_links": 1,
    }


def test_get_deadline_status_classifies_deadlines():
    from dashboard.dashboard_data import get_deadline_status

    assert get_deadline_status(
        "2026-10-21",
        today="2026-10-02",
    ) == {
        "status": "UPCOMING",
        "days": 19,
        "label": "19 days left",
    }

    assert get_deadline_status(
        "2026-10-02",
        today="2026-10-02",
    ) == {
        "status": "TODAY",
        "days": 0,
        "label": "Due today",
    }

    assert get_deadline_status(
        "2006-04-01",
        today="2026-10-02",
    ) == {
        "status": "EXPIRED",
        "days": -7489,
        "label": "Expired",
    }

    assert get_deadline_status(
        "",
        today="2026-10-02",
    ) == {
        "status": "MISSING",
        "days": None,
        "label": "No deadline",
    }

    assert get_deadline_status(
        "not-a-date",
        today="2026-10-02",
    ) == {
        "status": "INVALID",
        "days": None,
        "label": "Invalid deadline",
    }

def test_build_daily_run_audit_shows_date_reason_and_counts():
    from dashboard.dashboard_data import build_daily_run_audit

    records = [
        {
            "Timestamp": "2026-10-03T18:30:00",
            "Agent": "SYSTEM",
            "Action": "DAILY_RUN",
            "Records_Added": "0",
            "Notes": (
                "Queries=55 | Qualified=0 | Saved=0 | "
                "Duplicates=0 | Failed=16 | "
                "Reason=No qualified opportunities; pipeline failures=16"
            ),
        },
        {
            "Timestamp": "2026-10-02T18:30:00",
            "Agent": "SYSTEM",
            "Action": "DAILY_RUN",
            "Records_Added": "2",
            "Notes": (
                "Queries=55 | Qualified=2 | Saved=2 | "
                "Duplicates=0 | Failed=0 | "
                "Reason=Opportunities saved successfully"
            ),
        },
        {
            "Timestamp": "2026-10-03T19:00:00",
            "Agent": "SYSTEM",
            "Action": "OPPORTUNITY_CREATED",
            "Records_Added": "1",
            "Notes": "OPP-000015",
        },
    ]

    audit = build_daily_run_audit(records)

    assert audit == [
        {
            "Run Date": "2026-10-03",
            "Reason": (
                "No qualified opportunities; "
                "pipeline failures=16"
            ),
            "Qualified": 0,
            "Saved": 0,
            "Duplicates": 0,
            "Failed": 16,
        },
        {
            "Run Date": "2026-10-02",
            "Reason": "Opportunities saved successfully",
            "Qualified": 2,
            "Saved": 2,
            "Duplicates": 0,
            "Failed": 0,
        },
    ]



def test_load_activity_log_reads_activity_log_sheet():
    from unittest.mock import Mock

    from dashboard.dashboard_data import load_activity_log
    from config.constants import ACTIVITY_LOG_SHEET

    sheets_client = Mock()
    sheets_client.read_records.return_value = [
        {
            "Timestamp": "2026-10-03T18:30:00",
            "Agent": "SYSTEM",
            "Action": "DAILY_RUN",
            "Records_Added": "0",
            "Notes": "Reason=No qualified opportunities",
        }
    ]

    records = load_activity_log(sheets_client=sheets_client)

    assert records == sheets_client.read_records.return_value
    sheets_client.read_records.assert_called_once_with(ACTIVITY_LOG_SHEET)
