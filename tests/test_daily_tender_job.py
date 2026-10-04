import pytest

import jobs.daily_tender_job as daily_tender_job


def test_daily_job_creates_one_shared_search_budget_from_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "SERP_DAILY_REQUEST_LIMIT",
        "7",
    )

    captured_budgets = []

    def fake_run_livehooah_pipeline(
        search_budget=None,
    ):
        captured_budgets.append(
            search_budget
        )

        return {
            "meta": {},
            "opportunities": [],
        }

    monkeypatch.setattr(
        daily_tender_job,
        "run_livehooah_pipeline",
        fake_run_livehooah_pipeline,
    )

    result = daily_tender_job.run_daily_tender_job()

    assert result == {
        "meta": {},
        "opportunities": [],
    }

    assert len(captured_budgets) == 1

    budget = captured_budgets[0]

    assert budget.serp_limit == 7
    assert budget.serp_used == 0
    assert budget.serp_remaining == 7


def test_daily_job_disables_serp_when_limit_is_missing(
    monkeypatch,
):
    monkeypatch.delenv(
        "SERP_DAILY_REQUEST_LIMIT",
        raising=False,
    )

    captured_budgets = []

    def fake_run_livehooah_pipeline(
        search_budget=None,
    ):
        captured_budgets.append(
            search_budget
        )

        return {
            "meta": {},
            "opportunities": [],
        }

    monkeypatch.setattr(
        daily_tender_job,
        "run_livehooah_pipeline",
        fake_run_livehooah_pipeline,
    )

    daily_tender_job.run_daily_tender_job()

    assert len(captured_budgets) == 1

    budget = captured_budgets[0]

    assert budget.serp_limit == 0
    assert budget.can_use_serp() is False


@pytest.mark.parametrize(
    "configured_limit",
    [
        "not-a-number",
        "-1",
    ],
)
def test_daily_job_rejects_invalid_serp_limit(
    monkeypatch,
    configured_limit,
):
    monkeypatch.setenv(
        "SERP_DAILY_REQUEST_LIMIT",
        configured_limit,
    )

    pipeline_called = False

    def fake_run_livehooah_pipeline(
        search_budget=None,
    ):
        nonlocal pipeline_called
        pipeline_called = True

        return {
            "meta": {},
            "opportunities": [],
        }

    monkeypatch.setattr(
        daily_tender_job,
        "run_livehooah_pipeline",
        fake_run_livehooah_pipeline,
    )

    with pytest.raises(ValueError):
        daily_tender_job.run_daily_tender_job()

    assert pipeline_called is False

def test_daily_job_logs_audit_when_no_opportunities_are_saved(
    monkeypatch,
):
    monkeypatch.setenv(
        "SERP_DAILY_REQUEST_LIMIT",
        "12",
    )

    activity_calls = []

    class FakeSheetsClient:
        def log_activity(
            self,
            agent,
            action,
            records_added,
            notes="",
        ):
            activity_calls.append(
                {
                    "agent": agent,
                    "action": action,
                    "records_added": records_added,
                    "notes": notes,
                }
            )

    def fake_run_livehooah_pipeline(
        search_budget=None,
    ):
        return {
            "meta": {
                "total_queries": 55,
                "total_found": 0,
                "total_saved": 0,
                "total_duplicates": 0,
                "total_failed": 16,
            },
            "opportunities": [],
        }

    monkeypatch.setattr(
        daily_tender_job,
        "run_livehooah_pipeline",
        fake_run_livehooah_pipeline,
    )
    monkeypatch.setattr(
        daily_tender_job,
        "SheetsClient",
        FakeSheetsClient,
        raising=False,
    )

    daily_tender_job.run_daily_tender_job()

    assert activity_calls == [
        {
            "agent": "SYSTEM",
            "action": "DAILY_RUN",
            "records_added": 0,
            "notes": (
                "Queries=55 | Qualified=0 | Saved=0 | "
                "Duplicates=0 | Failed=16 | "
                "Reason=No qualified opportunities; pipeline failures=16"
            ),
        }
    ]
