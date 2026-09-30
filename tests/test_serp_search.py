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

class SuccessfulGoogleSearch:
    calls = []

    def __init__(self, params):
        self.params = params
        type(self).calls.append(params)

    def get_dict(self):
        return {
            "organic_results": [
                {
                    "title": "Structural Audit Consultancy Tender",
                    "snippet": "Tender for structural audit consultancy services",
                    "link": "https://example.gov.in/tender/123",
                }
            ]
        }


class Cp1252Stdout:
    def write(self, text):
        text.encode("cp1252")
        return len(text)

    def flush(self):
        pass


def test_search_diagnostics_do_not_block_provider_on_cp1252_stdout(
    monkeypatch,
):
    SuccessfulGoogleSearch.calls = []

    monkeypatch.setattr(
        serp_search.os,
        "getenv",
        lambda key: "fake-test-key",
    )
    monkeypatch.setattr(
        serp_search,
        "GoogleSearch",
        SuccessfulGoogleSearch,
    )
    monkeypatch.setattr(
        "sys.stdout",
        Cp1252Stdout(),
    )

    search = serp_search.SerpSearch()

    results = search.search(
        "structural audit 2026"
    )

    assert len(SuccessfulGoogleSearch.calls) == 1
    assert (
        SuccessfulGoogleSearch.calls[0]["q"]
        == "structural audit 2026"
    )
    assert len(results) == 1
    assert (
        results[0]["title"]
        == "Structural Audit Consultancy Tender"
    )
