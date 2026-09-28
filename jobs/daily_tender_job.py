import os

from core.services.opportunity_pipeline import run_livehooah_pipeline
from core.services.search_budget import SearchBudget


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

    return run_livehooah_pipeline(
        search_budget=budget
    )
