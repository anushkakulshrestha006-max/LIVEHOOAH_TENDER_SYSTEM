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

def test_discover_navigation_links_rejects_archive_page():
    scraper = ScraperSearch()

    html = """
    <html>
        <body>
            <a href="/current-tenders.php">
                Current Tenders
            </a>

            <a href="/tenders-archive.php">
                Old Tenders
            </a>
        </body>
    </html>
    """

    links = scraper._discover_navigation_links(
        html,
        "https://example.gov.in/tenders.php",
    )

    discovered_urls = [
        url
        for _, url, _ in links
    ]

    assert (
        "https://example.gov.in/current-tenders.php"
        in discovered_urls
    )

    assert (
        "https://example.gov.in/tenders-archive.php"
        not in discovered_urls
    )

def test_bad_url_allows_tender_document_inside_archive_directory():
    scraper = ScraperSearch()

    url = (
        "https://example.gov.in/"
        "public/storage/tenders_archives/"
        "NIT_123456.pdf"
    )

    assert scraper._is_bad_url(url) is False


def test_crawl_source_does_not_fetch_archive_navigation_page(
    monkeypatch,
):
    scraper = ScraperSearch()

    fetched_urls = []

    pages = {
        "https://example.gov.in": """
            <html>
                <body>
                    <a href="/current-tenders.php">
                        Current Tenders
                    </a>
                    <a href="/tenders-archive.php">
                        Old Tenders
                    </a>
                </body>
            </html>
        """,
        "https://example.gov.in/current-tenders.php": """
            <html>
                <body>
                    Current procurement page
                </body>
            </html>
        """,
        "https://example.gov.in/tenders-archive.php": """
            <html>
                <body>
                    Old procurement records
                </body>
            </html>
        """,
    }

    def fake_fetch_page(url):
        fetched_urls.append(url)
        return pages.get(url)

    monkeypatch.setattr(
        scraper,
        "_fetch_page",
        fake_fetch_page,
    )

    scraper._crawl_source(
        "https://example.gov.in",
        "structural consultancy",
    )

    assert (
        "https://example.gov.in/current-tenders.php"
        in fetched_urls
    )

    assert (
        "https://example.gov.in/tenders-archive.php"
        not in fetched_urls
    )


def test_extract_links_accepts_generic_download_with_strong_tender_row_context():
    scraper = ScraperSearch()

    html = """
    <html>
        <body>
            <table>
                <tr>
                    <td>
                        Tender for appointment of structural consultant
                        for proof checking and design verification
                    </td>
                    <td>
                        <a href="/docs/proof-checking.pdf">
                            Download
                        </a>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """

    opportunities = scraper._extract_links(
        html,
        "https://example.gov.in/tenders",
        "proof checking consultant",
    )

    assert len(opportunities) == 1

    opportunity = opportunities[0]

    assert opportunity["source_url"] == (
        "https://example.gov.in/docs/proof-checking.pdf"
    )

    assert (
        "proof checking"
        in opportunity["title"].lower()
    )

    assert (
        "structural consultant"
        in opportunity["title"].lower()
    )


def test_extract_links_rejects_generic_download_without_livehooah_context():
    scraper = ScraperSearch()

    html = """
    <html>
        <body>
            <table>
                <tr>
                    <td>
                        General procurement notice for
                        cafeteria equipment and supplies
                    </td>
                    <td>
                        <a href="/docs/cafeteria-equipment.pdf">
                            Download
                        </a>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """

    opportunities = scraper._extract_links(
        html,
        "https://example.gov.in/tenders",
        "proof checking consultant",
    )

    assert opportunities == []

def test_crawl_source_stops_when_source_time_budget_is_exhausted(
    monkeypatch,
):
    scraper = ScraperSearch()

    scraper.MAX_SOURCE_CRAWL_SECONDS = 20

    fetched_urls = []

    pages = {
        "https://example.gov.in": """
            <html>
                <body>
                    <a href="/tenders">
                        Current Tenders
                    </a>
                </body>
            </html>
        """,
        "https://example.gov.in/tenders": """
            <html>
                <body>
                    <a href="/procurement">
                        Procurement Notices
                    </a>
                </body>
            </html>
        """,
    }

    def fake_fetch_page(url):
        fetched_urls.append(url)
        return pages.get(url)

    monotonic_values = iter([
        100.0,
        105.0,
        121.0,
    ])

    monkeypatch.setattr(
        scraper,
        "_fetch_page",
        fake_fetch_page,
    )

    monkeypatch.setattr(
        "core.services.scraper_search.time.monotonic",
        lambda: next(monotonic_values),
    )

    scraper._crawl_source(
        "https://example.gov.in",
        "structural consultancy tender",
    )

    assert fetched_urls == [
        "https://example.gov.in",
    ]
