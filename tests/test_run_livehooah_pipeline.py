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
