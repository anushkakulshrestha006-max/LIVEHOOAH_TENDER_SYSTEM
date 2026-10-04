from datetime import date, datetime


def _is_true(value):
    if value is True:
        return True

    if isinstance(value, str):
        return value.strip().upper() == "TRUE"

    return False


def build_dashboard_metrics(records, today=None):
    """
    Build top-level dashboard KPI counts from opportunity records.
    """

    if today is None:
        today_date = date.today()
    elif isinstance(today, str):
        today_date = datetime.strptime(
            today,
            "%Y-%m-%d",
        ).date()
    else:
        today_date = today

    total = len(records)

    qualified = sum(
        1
        for record in records
        if _is_true(
            record.get("Qualified")
        )
    )

    high_priority = sum(
        1
        for record in records
        if str(
            record.get("Priority", "")
        ).strip().upper() == "HIGH"
    )

    upcoming_deadlines = 0

    for record in records:
        deadline = str(
            record.get("Deadline", "")
        ).strip()

        if not deadline:
            continue

        try:
            deadline_date = datetime.strptime(
                deadline,
                "%Y-%m-%d",
            ).date()
        except ValueError:
            continue

        if deadline_date >= today_date:
            upcoming_deadlines += 1

    return {
        "total": total,
        "qualified": qualified,
        "high_priority": high_priority,
        "upcoming_deadlines": upcoming_deadlines,
    }


def filter_opportunities(
    records,
    priority=None,
    status=None,
    search=None,
):
    """
    Filter dashboard opportunity records without mutating them.
    """

    filtered = list(records)

    if priority:
        expected_priority = str(
            priority
        ).strip().upper()

        filtered = [
            record
            for record in filtered
            if str(
                record.get("Priority", "")
            ).strip().upper() == expected_priority
        ]

    if status:
        expected_status = str(
            status
        ).strip().upper()

        filtered = [
            record
            for record in filtered
            if str(
                record.get("Opportunity_Status", "")
            ).strip().upper() == expected_status
        ]

    if search:
        query = str(
            search
        ).strip().lower()

        searchable_fields = (
            "Opportunity_ID",
            "Title",
            "Organization",
            "Location",
            "Type",
            "Service_Category",
        )

        filtered = [
            record
            for record in filtered
            if any(
                query in str(
                    record.get(field, "")
                ).lower()
                for field in searchable_fields
            )
        ]

    return filtered


def sort_opportunities_by_deadline(records):
    """
    Sort opportunities by nearest valid ISO deadline.

    Blank or invalid deadlines are placed at the end.
    """

    def deadline_key(record):
        deadline = str(
            record.get("Deadline", "")
        ).strip()

        try:
            parsed = datetime.strptime(
                deadline,
                "%Y-%m-%d",
            ).date()

            return (
                0,
                parsed,
            )
        except ValueError:
            return (
                1,
                date.max,
            )

    return sorted(
        records,
        key=deadline_key,
    )


def load_opportunities(sheets_client=None):
    """
    Load opportunity records through the existing SheetsClient contract.
    """

    if sheets_client is None:
        from sheets.sheets_client import SheetsClient

        sheets_client = SheetsClient()

    from config.constants import OPPORTUNITIES_SHEET

    records = sheets_client.read_records(
        OPPORTUNITIES_SHEET
    )

    return records or []


def load_activity_log(sheets_client=None):
    if sheets_client is None:
        from sheets.sheets_client import SheetsClient

        sheets_client = SheetsClient()

    from config.constants import ACTIVITY_LOG_SHEET

    return sheets_client.read_records(ACTIVITY_LOG_SHEET) or []

def build_daily_run_audit(records):
    """
    Build dashboard-ready daily run audit records from Activity_Log rows.
    """

    audit = []

    for record in records:
        if (
            str(record.get("Agent", "")).strip().upper() != "SYSTEM"
            or str(record.get("Action", "")).strip().upper() != "DAILY_RUN"
        ):
            continue

        timestamp = str(
            record.get("Timestamp", "")
        ).strip()

        try:
            run_date = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            ).date().isoformat()
        except ValueError:
            continue

        notes = str(
            record.get("Notes", "")
        ).strip()

        values = {}

        for part in notes.split(" | "):
            if "=" not in part:
                continue

            key, value = part.split("=", 1)
            values[key.strip()] = value.strip()

        try:
            qualified = int(values.get("Qualified", 0))
            saved = int(values.get("Saved", 0))
            duplicates = int(values.get("Duplicates", 0))
            failed = int(values.get("Failed", 0))
        except ValueError:
            continue

        reason = values.get(
            "Reason",
            "No reason recorded",
        )

        audit.append(
            {
                "Run Date": run_date,
                "Reason": reason,
                "Qualified": qualified,
                "Saved": saved,
                "Duplicates": duplicates,
                "Failed": failed,
            }
        )

    return sorted(
        audit,
        key=lambda record: record["Run Date"],
        reverse=True,
    )

def build_data_quality_metrics(records):
    """
    Count dashboard-visible data quality issues without modifying records.
    """

    missing_deadlines = 0
    invalid_deadlines = 0
    suspicious_locations = 0
    missing_source_links = 0

    suspicious_location_phrases = (
        "http://",
        "https://",
        "www.",
        "proposal may be",
        "registration no.",
        "tax department",
        "service tax",
    )

    for record in records:
        deadline = str(
            record.get("Deadline", "")
        ).strip()

        if not deadline:
            missing_deadlines += 1
        else:
            try:
                datetime.strptime(
                    deadline,
                    "%Y-%m-%d",
                )
            except ValueError:
                invalid_deadlines += 1

        location = str(
            record.get("Location", "")
        ).strip().lower()

        if location and any(
            phrase in location
            for phrase in suspicious_location_phrases
        ):
            suspicious_locations += 1

        source_link = str(
            record.get("Source_Link", "")
        ).strip()

        if not source_link:
            missing_source_links += 1

    return {
        "missing_deadlines": missing_deadlines,
        "invalid_deadlines": invalid_deadlines,
        "suspicious_locations": suspicious_locations,
        "missing_source_links": missing_source_links,
    }


def get_deadline_status(deadline, today=None):
    """
    Classify a tender deadline for dashboard presentation.
    """

    if today is None:
        today_date = date.today()
    elif isinstance(today, str):
        today_date = datetime.strptime(
            today,
            "%Y-%m-%d",
        ).date()
    else:
        today_date = today

    deadline_text = str(
        deadline or ""
    ).strip()

    if not deadline_text:
        return {
            "status": "MISSING",
            "days": None,
            "label": "No deadline",
        }

    try:
        deadline_date = datetime.strptime(
            deadline_text,
            "%Y-%m-%d",
        ).date()
    except ValueError:
        return {
            "status": "INVALID",
            "days": None,
            "label": "Invalid deadline",
        }

    days = (
        deadline_date - today_date
    ).days

    if days < 0:
        return {
            "status": "EXPIRED",
            "days": days,
            "label": "Expired",
        }

    if days == 0:
        return {
            "status": "TODAY",
            "days": 0,
            "label": "Due today",
        }

    return {
        "status": "UPCOMING",
        "days": days,
        "label": f"{days} days left",
    }
