import os

from core.services.opportunity_pipeline import run_livehooah_pipeline
from core.services.search_budget import SearchBudget
from sheets.sheets_client import SheetsClient


def run_daily_tender_job():
    configured_limit = os.getenv(
        "SERP_DAILY_REQUEST_LIMIT",
        "0",
    )

    try:
        serp_limit = int(
            configured_limit
        )
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "SERP_DAILY_REQUEST_LIMIT must be a non-negative integer"
        ) from exc

    budget = SearchBudget(
        serp_limit=serp_limit
    )

    result = run_livehooah_pipeline(
        search_budget=budget
    )

    meta = result.get("meta", {})
    total_found = meta.get("total_found", 0)
    total_saved = meta.get("total_saved", 0)
    total_duplicates = meta.get("total_duplicates", 0)
    total_failed = meta.get("total_failed", 0)

    if total_saved > 0:
        reason = "Opportunities saved successfully"
    elif total_found == 0 and total_failed > 0:
        reason = f"No qualified opportunities; pipeline failures={total_failed}"
    elif total_found == 0:
        reason = "No qualified opportunities"
    elif total_duplicates == total_found:
        reason = "All qualified opportunities were duplicates"
    elif total_failed > 0:
        reason = "No opportunities saved; pipeline failures occurred"
    else:
        reason = "No opportunities saved"

    SheetsClient().log_activity(
        agent="SYSTEM",
        action="DAILY_RUN",
        records_added=meta.get("total_saved", 0),
        notes=(
            f"Queries={meta.get('total_queries', 0)} | "
            f"Qualified={meta.get('total_found', 0)} | "
            f"Saved={meta.get('total_saved', 0)} | "
            f"Duplicates={meta.get('total_duplicates', 0)} | "
            f"Failed={total_failed} | "
            f"Reason={reason}"
        ),
    )

    return result
