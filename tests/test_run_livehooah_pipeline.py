from unittest.mock import patch

from core.services.opportunity_pipeline import run_livehooah_pipeline


def test_run_livehooah_pipeline_aggregates_query_results():
    query_results = {
        "query-one": {
            "meta": {
                "total_found": 2,
                "saved": 1,
                "duplicates": 1,
                "failed": 0,
            },
            "opportunities": [
                {"title": "Opportunity One"},
                {"title": "Opportunity Two"},
            ],
        },
        "query-two": {
            "meta": {
                "total_found": 1,
                "saved": 0,
                "duplicates": 0,
                "failed": 1,
            },
            "opportunities": [
                {"title": "Opportunity Three"},
            ],
        },
    }

    def mock_run_pipeline(query):
        return query_results[query]

    with patch(
        "core.services.opportunity_pipeline.LIVEHOOAH_QUERIES",
        ["query-one", "query-two"],
    ), patch(
        "core.services.opportunity_pipeline.run_pipeline",
        side_effect=mock_run_pipeline,
    ) as mock_run_pipeline:

        result = run_livehooah_pipeline()

    assert [call.args[0] for call in mock_run_pipeline.call_args_list] == [
        "query-one",
        "query-two",
    ]

    assert result["meta"] == {
        "total_queries": 2,
        "total_found": 3,
        "total_saved": 1,
        "total_duplicates": 1,
        "total_failed": 1,
    }

    assert result["opportunities"] == [
        {"title": "Opportunity One"},
        {"title": "Opportunity Two"},
        {"title": "Opportunity Three"},
    ]


def test_run_livehooah_pipeline_reuses_one_search_budget_for_all_queries():
    from core.services.search_budget import SearchBudget

    budget = SearchBudget(
        serp_limit=7
    )

    captured_budgets = []

    def mock_run_pipeline(
        query,
        search_budget=None,
    ):
        captured_budgets.append(
            search_budget
        )

        return {
            "meta": {
                "total_found": 0,
                "saved": 0,
                "duplicates": 0,
                "failed": 0,
            },
            "opportunities": [],
        }

    with patch(
        "core.services.opportunity_pipeline.LIVEHOOAH_QUERIES",
        ["query-one", "query-two"],
    ), patch(
        "core.services.opportunity_pipeline.run_pipeline",
        side_effect=mock_run_pipeline,
    ) as mock_pipeline:

        result = run_livehooah_pipeline(
            search_budget=budget
        )

    assert mock_pipeline.call_count == 2

    assert len(captured_budgets) == 2
    assert captured_budgets[0] is budget
    assert captured_budgets[1] is budget
    assert captured_budgets[0] is captured_budgets[1]

    assert result["meta"]["total_queries"] == 2
    assert result["opportunities"] == []
