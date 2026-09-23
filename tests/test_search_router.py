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

