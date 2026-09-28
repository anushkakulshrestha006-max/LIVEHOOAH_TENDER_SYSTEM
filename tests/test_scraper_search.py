from core.services.scraper_search import ScraperSearch


def test_fetch_page_reuses_cached_html_across_calls(
    monkeypatch,
):
    scraper = ScraperSearch()

    request_calls = []

    class FakeResponse:
        status_code = 200
        headers = {
            "Content-Type": "text/html",
        }
        text = "<html><body>Tender page</body></html>"

    def fake_get(
        url,
        headers,
        timeout,
        allow_redirects,
    ):
        request_calls.append(
            url
        )

        return FakeResponse()

    monkeypatch.setattr(
        "core.services.scraper_search.requests.get",
        fake_get,
    )

    url = "https://example.gov.in/tenders"

    first = scraper._fetch_page(
        url
    )

    second = scraper._fetch_page(
        url
    )

    assert first == FakeResponse.text
    assert second == FakeResponse.text

    assert request_calls == [
        url,
    ]


def test_fetch_page_caches_failed_http_response(
    monkeypatch,
):
    scraper = ScraperSearch()

    request_calls = []

    class FakeResponse:
        status_code = 503
        headers = {
            "Content-Type": "text/html",
        }
        text = "Service Unavailable"

    def fake_get(
        url,
        headers,
        timeout,
        allow_redirects,
    ):
        request_calls.append(
            url
        )

        return FakeResponse()

    monkeypatch.setattr(
        "core.services.scraper_search.requests.get",
        fake_get,
    )

    url = "https://example.gov.in/tenders"

    first = scraper._fetch_page(
        url
    )

    second = scraper._fetch_page(
        url
    )

    assert first is None
    assert second is None

    assert request_calls == [
        url,
    ]


def test_fetch_page_caches_other_failed_fetches(
    monkeypatch,
):
    scenarios = [
        "non_html",
        "request_exception",
    ]

    for scenario in scenarios:
        scraper = ScraperSearch()

        request_calls = []

        def fake_get(
            url,
            headers,
            timeout,
            allow_redirects,
        ):
            request_calls.append(
                url
            )

            if scenario == "request_exception":
                from requests import RequestException

                raise RequestException(
                    "simulated request failure"
                )

            class FakeResponse:
                status_code = 200
                headers = {
                    "Content-Type": "application/pdf",
                }
                text = "not html"

            return FakeResponse()

        monkeypatch.setattr(
            "core.services.scraper_search.requests.get",
            fake_get,
        )

        url = (
            "https://example.gov.in/"
            f"{scenario}"
        )

        first = scraper._fetch_page(
            url
        )

        second = scraper._fetch_page(
            url
        )

        assert first is None
        assert second is None

        assert request_calls == [
            url,
        ], scenario
