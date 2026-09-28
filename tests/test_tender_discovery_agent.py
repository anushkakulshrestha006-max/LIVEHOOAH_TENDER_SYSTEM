
from agents import tender_discovery_agent


def test_run_tender_discovery_prefixes_and_aggregates_queries(monkeypatch):
    searched_queries = []

    class FakeRouter:
        def search(self, query):
            searched_queries.append(query)
            return [
                {
                    "title": f"Result for {query}",
                    "source_url": f"https://example.gov.in/{len(searched_queries)}",
                }
            ]

    monkeypatch.setattr(
        tender_discovery_agent,
        "SearchRouter",
        FakeRouter,
    )

    result = tender_discovery_agent.run_tender_discovery(
        "road construction"
    )

    assert result["status"] == "success"
    assert len(result["opportunities"]) == len(searched_queries)
    assert len(searched_queries) == len(
        tender_discovery_agent.expand_query("road construction")
    )

    assert (
        searched_queries[0]
        == "structural engineering consultancy road construction"
    )


def test_run_tender_discovery_preserves_aligned_query(monkeypatch):
    searched_queries = []

    class FakeRouter:
        def search(self, query):
            searched_queries.append(query)
            return []

    monkeypatch.setattr(
        tender_discovery_agent,
        "SearchRouter",
        FakeRouter,
    )

    result = tender_discovery_agent.run_tender_discovery(
        "structural audit"
    )

    assert result == {
        "status": "success",
        "opportunities": [],
    }

    assert searched_queries[0] == "structural audit"


def test_run_tender_discovery_continues_after_search_failure(monkeypatch):
    searched_queries = []

    class FakeRouter:
        def search(self, query):
            searched_queries.append(query)

            if len(searched_queries) == 1:
                raise RuntimeError("simulated search failure")

            return [
                {
                    "title": "Structural Audit Tender",
                    "source_url": (
                        "https://example.gov.in/tender/123"
                    ),
                }
            ]

    monkeypatch.setattr(
        tender_discovery_agent,
        "SearchRouter",
        FakeRouter,
    )

    result = tender_discovery_agent.run_tender_discovery(
        "structural audit"
    )

    assert result["status"] == "success"
    assert len(searched_queries) == len(
        tender_discovery_agent.expand_query("structural audit")
    )
    assert len(result["opportunities"]) == len(searched_queries) - 1
    assert all(
        opportunity == {
            "title": "Structural Audit Tender",
            "source_url": "https://example.gov.in/tender/123",
        }
        for opportunity in result["opportunities"]
    )

def test_run_tender_discovery_passes_shared_search_budget_to_router(monkeypatch):
    from core.services.search_budget import SearchBudget

    captured_budgets = []

    class FakeRouter:
        def __init__(self, search_budget=None):
            captured_budgets.append(
                search_budget
            )

        def search(self, query):
            return []

    monkeypatch.setattr(
        tender_discovery_agent,
        "SearchRouter",
        FakeRouter,
    )

    budget = SearchBudget(
        serp_limit=3
    )

    result = tender_discovery_agent.run_tender_discovery(
        "structural audit",
        search_budget=budget,
    )

    assert result == {
        "status": "success",
        "opportunities": [],
    }

    assert len(captured_budgets) == 1
    assert captured_budgets[0] is budget
