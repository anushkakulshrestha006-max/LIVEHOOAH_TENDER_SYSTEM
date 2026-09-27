import pytest

from core.services import serp_search


class FakeGoogleSearch:
    def __init__(self, params):
        self.params = params

    def get_dict(self):
        return {
            "error": "Simulated provider quota exhausted",
        }


def test_search_raises_when_provider_returns_error_payload(monkeypatch):
    monkeypatch.setattr(
        serp_search.os,
        "getenv",
        lambda key: "fake-test-key",
    )
    monkeypatch.setattr(
        serp_search,
        "GoogleSearch",
        FakeGoogleSearch,
    )

    search = serp_search.SerpSearch()

    with pytest.raises(
        RuntimeError,
        match="Simulated provider quota exhausted",
    ):
        search.search(
            "structural consultancy tender"
        )
