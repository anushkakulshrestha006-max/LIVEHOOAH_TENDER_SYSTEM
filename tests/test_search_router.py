import pytest

from core.services.search_router import (
    MIN_DISCOVERY_SCORE,
    SearchRouter,
)


def make_router():
    router = SearchRouter.__new__(SearchRouter)
    return router


def test_contains_keyword_uses_word_boundaries():
    assert SearchRouter._contains_keyword(
        "structural consultant required",
        "consultant",
    )

    assert not SearchRouter._contains_keyword(
        "consultants required",
        "consultant",
    )


def test_canonicalize_url_removes_tracking_and_fragment():
    result = SearchRouter._canonicalize_url(
        "HTTPS://EXAMPLE.GOV.IN/tenders/?utm_source=google&b=2&a=1#section"
    )

    assert result == (
        "https://example.gov.in/tenders?a=1&b=2"
    )


def test_canonicalize_title_normalizes_case_punctuation_and_whitespace():
    result = SearchRouter._canonicalize_title(
        "  Structural-Consultancy!!!   Services  "
    )

    assert result == "structural consultancy services"


def test_score_opportunity_accepts_structural_tender():
    router = make_router()

    is_valid, score = router._score_opportunity(
        {
            "title": "Structural Engineering Consultancy Tender",
            "description": "Tender for structural design and consultancy services",
            "source_url": "https://example.gov.in/tender/123",
        }
    )

    assert is_valid
    assert score >= MIN_DISCOVERY_SCORE


def test_score_opportunity_rejects_without_tender_signal():
    router = make_router()

    is_valid, score = router._score_opportunity(
        {
            "title": "Structural Engineering Consultancy Services",
            "description": "Structural design and consultancy services",
            "source_url": "https://example.gov.in/services/123",
        }
    )

    assert not is_valid
    assert score == 0


def test_score_opportunity_rejects_blocked_portal():
    router = make_router()

    is_valid, score = router._score_opportunity(
        {
            "title": "Structural Engineering Tender",
            "description": "Tender for structural consultancy",
            "source_url": "https://bidassist.com/tender/123",
        }
    )

    assert not is_valid
    assert score == 0


def test_score_opportunity_rejects_unrelated_service_without_support():
    router = make_router()

    is_valid, score = router._score_opportunity(
        {
            "title": "Housekeeping Tender",
            "description": "Housekeeping and cleaning services",
            "source_url": "https://example.gov.in/tender/123",
        }
    )

    assert not is_valid
    assert score == 0


def test_score_opportunity_keeps_strong_structural_signal_with_unrelated_term():
    router = make_router()

    is_valid, score = router._score_opportunity(
        {
            "title": "Structural Audit and Housekeeping Services Tender",
            "description": "Structural audit consultancy for an existing building",
            "source_url": "https://example.gov.in/tender/123",
        }
    )

    assert is_valid
    assert score >= MIN_DISCOVERY_SCORE


def test_search_deduplicates_and_attaches_intelligence():
    router = make_router()

    class FakeSearch:
        def __init__(self, results):
            self.results = results

        def search(self, query):
            return list(self.results)

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
                "service_category": "structural consultancy",
            }

    router.serp_search = FakeSearch(
        [
            {
                "title": "Structural Consultancy Tender",
                "description": "Tender for structural consultancy",
                "source_url": (
                    "https://example.gov.in/tender/123"
                    "?utm_source=google"
                ),
            }
        ]
    )

    router.scraper_search = FakeSearch(
        [
            {
                "title": "Structural Consultancy Tender",
                "description": "Tender for structural consultancy",
                "source_url": "https://example.gov.in/tender/123",
            }
        ]
    )

    router.intelligence = FakeIntelligence()

    result = router.search("structural consultancy tender")

    assert len(result) == 1
    assert result[0]["discovery_score"] >= MIN_DISCOVERY_SCORE
    assert result[0]["discovery_source"] == "serp"
    assert result[0]["intelligence"]["is_relevant"] is True


def test_search_rejects_irrelevant_candidates_before_intelligence():
    router = make_router()

    class FakeSearch:
        def search(self, query):
            return [
                {
                    "title": "Housekeeping Tender",
                    "description": "Housekeeping services",
                    "source_url": "https://example.gov.in/tender/low",
                }
            ]

    class FakeIntelligence:
        def analyze(self, opportunity):
            pytest.fail("Intelligence should not run for rejected candidate")

    router.serp_search = FakeSearch()
    router.scraper_search = FakeSearch()
    router.intelligence = FakeIntelligence()

    result = router.search("structural consultancy tender")

    assert result == []




def test_search_router_initializes_scraper_when_serp_is_unavailable(monkeypatch):
    from core.services import search_router

    class FailingSerpSearch:
        def __init__(self):
            raise ValueError("SERPAPI_KEY not found in environment")

    class FakeScraperSearch:
        def search(self, query):
            return [
                {
                    "title": "Structural Consultancy Tender",
                    "description": "Tender for structural consultancy services",
                    "source_url": "https://example.gov.in/tender/123",
                }
            ]

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
            }

    monkeypatch.setattr(
        search_router,
        "SerpSearch",
        FailingSerpSearch,
    )
    monkeypatch.setattr(
        search_router,
        "ScraperSearch",
        FakeScraperSearch,
    )
    monkeypatch.setattr(
        search_router,
        "TenderIntelligence",
        FakeIntelligence,
    )

    router = search_router.SearchRouter()

    assert isinstance(router.scraper_search, FakeScraperSearch)
    assert isinstance(router.intelligence, FakeIntelligence)

    result = router.search("structural consultancy tender")

    assert len(result) == 1
    assert result[0]["discovery_source"] == "scraper"
    assert result[0]["source_url"] == "https://example.gov.in/tender/123"
    assert result[0]["intelligence"]["is_relevant"] is True


def test_search_router_continues_with_scraper_after_serp_runtime_failure():
    from core.services.search_router import SearchRouter

    class FailingSearch:
        def search(self, query):
            raise RuntimeError(
                "SERP provider error: Simulated provider quota exhausted"
            )

    class FakeScraperSearch:
        def search(self, query):
            return [
                {
                    "title": "Structural Consultancy Tender",
                    "description": "Tender for structural consultancy services",
                    "source_url": "https://example.gov.in/tender/456",
                }
            ]

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
            }

    router = SearchRouter.__new__(SearchRouter)
    router.serp_search = FailingSearch()
    router.scraper_search = FakeScraperSearch()
    router.intelligence = FakeIntelligence()

    result = router.search(
        "structural consultancy tender"
    )

    assert len(result) == 1
    assert result[0]["discovery_source"] == "scraper"
    assert result[0]["source_url"] == "https://example.gov.in/tender/456"
    assert result[0]["intelligence"]["is_relevant"] is True


def test_search_router_respects_shared_serp_budget():
    from core.services.search_budget import SearchBudget
    from core.services.search_router import SearchRouter

    class FakeSerpSearch:
        def __init__(self):
            self.calls = []

        def search(self, query):
            self.calls.append(query)
            return []

    class FakeScraperSearch:
        def __init__(self):
            self.calls = []

        def search(self, query):
            self.calls.append(query)
            return []

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
            }

    budget = SearchBudget(
        serp_limit=1
    )

    router = SearchRouter.__new__(SearchRouter)
    router.serp_search = FakeSerpSearch()
    router.scraper_search = FakeScraperSearch()
    router.intelligence = FakeIntelligence()
    router.search_budget = budget

    router.search(
        "structural consultancy tender"
    )

    router.search(
        "structural audit tender"
    )

    assert router.serp_search.calls == [
        "structural consultancy tender"
    ]

    assert router.scraper_search.calls == [
        "structural consultancy tender",
        "structural audit tender",
    ]

    assert budget.serp_used == 1
    assert budget.serp_remaining == 0


def test_search_router_disables_shared_serp_budget_after_runtime_failure():
    from core.services.search_budget import SearchBudget
    from core.services.search_router import SearchRouter

    class FailingSerpSearch:
        def __init__(self):
            self.calls = []

        def search(self, query):
            self.calls.append(query)
            raise RuntimeError(
                "SERP provider error: Simulated provider quota exhausted"
            )

    class FakeScraperSearch:
        def __init__(self):
            self.calls = []

        def search(self, query):
            self.calls.append(query)
            return []

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
            }

    budget = SearchBudget(
        serp_limit=5
    )

    router = SearchRouter.__new__(SearchRouter)
    router.serp_search = FailingSerpSearch()
    router.scraper_search = FakeScraperSearch()
    router.intelligence = FakeIntelligence()
    router.search_budget = budget

    router.search(
        "structural consultancy tender"
    )

    router.search(
        "structural audit tender"
    )

    assert router.serp_search.calls == [
        "structural consultancy tender"
    ]

    assert router.scraper_search.calls == [
        "structural consultancy tender",
        "structural audit tender",
    ]

    assert budget.serp_used == 1
    assert budget.serp_remaining == 4
    assert budget.can_use_serp() is False

def test_search_router_logs_raw_serp_result_count(caplog):
    import logging

    router = make_router()

    class FakeSerpSearch:
        def search(self, query):
            return [
                {
                    "title": "Structural Consultancy Tender",
                    "description": "Tender for structural consultancy services",
                    "source_url": "https://example.gov.in/tender/123",
                },
                {
                    "title": "Structural Audit Tender",
                    "description": "Tender for structural audit consultancy",
                    "source_url": "https://example.gov.in/tender/456",
                },
            ]

    class FakeScraperSearch:
        def search(self, query):
            return []

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
            }

    router.serp_search = FakeSerpSearch()
    router.scraper_search = FakeScraperSearch()
    router.intelligence = FakeIntelligence()
    router.search_budget = None

    with caplog.at_level(logging.INFO):
        result = router.search(
            "structural consultancy tender"
        )

    assert len(result) == 2

    assert (
        "SERP raw results | "
        "query=structural consultancy tender | "
        "count=2"
    ) in caplog.text

def test_search_router_logs_discovery_filter_diagnostics(caplog):
    import logging

    router = make_router()

    class FakeSerpSearch:
        def search(self, query):
            return [
                {
                    "title": "Structural Consultancy Tender",
                    "description": "Tender for structural consultancy services",
                    "source_url": "https://example.gov.in/tender/accepted",
                },
                {
                    "title": "Housekeeping Tender",
                    "description": "Housekeeping and cleaning services",
                    "source_url": "https://example.gov.in/tender/rejected",
                },
            ]

    class FakeScraperSearch:
        def search(self, query):
            return []

    class FakeIntelligence:
        def analyze(self, opportunity):
            return {
                "is_relevant": True,
            }

    router.serp_search = FakeSerpSearch()
    router.scraper_search = FakeScraperSearch()
    router.intelligence = FakeIntelligence()
    router.search_budget = None

    with caplog.at_level(logging.INFO):
        result = router.search(
            "structural consultancy tender"
        )

    assert len(result) == 1

    assert (
        "Discovery filter diagnostics | "
        "total=2 | rejected_invalid=1 | "
        "rejected_below_score=0 | accepted=1"
    ) in caplog.text
