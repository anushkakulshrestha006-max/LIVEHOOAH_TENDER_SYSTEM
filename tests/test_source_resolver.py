from dataclasses import dataclass

import requests

from core.services.source_resolver import SourceResolver


@dataclass
class FakeResponse:
    """
    Minimal test-only replacement for requests.Response.
    """

    url: str
    text: str
    content_type: str = "text/html"

    def __post_init__(self):
        self.headers = {
            "Content-Type": self.content_type,
        }

    def raise_for_status(self):
        return None


class FakeSession:
    """
    Test-only HTTP session.

    No real network request is made.
    """

    def __init__(
        self,
        response=None,
        exception=None,
    ):
        self.response = response
        self.exception = exception
        self.headers = {}

    def get(
        self,
        url,
        timeout=None,
        allow_redirects=True,
    ):
        if self.exception:
            raise self.exception

        return self.response


def run_test(
    name,
    condition,
):
    status = "PASS" if condition else "FAIL"
    print(f"{name:45}: {status}")
    return condition


def main():
    print("=" * 80)
    print("SOURCE RESOLVER TEST")
    print("=" * 80)

    resolver = SourceResolver()

    results = []

    # ------------------------------------------------------------------
    # 1. DIRECT PDF URL
    # ------------------------------------------------------------------

    direct_pdf = (
        "https://example.gov.in/tenders/"
        "structural-engineer-rfp.pdf"
    )

    result = resolver.resolve(direct_pdf)

    results.append(
        run_test(
            "Direct PDF URL returned unchanged",
            result == direct_pdf,
        )
    )

    # ------------------------------------------------------------------
    # 2. HTML PAGE WITH RELEVANT TENDER PDF
    # ------------------------------------------------------------------

    page_url = (
        "https://example.gov.in/tenders/"
        "structural-consultancy"
    )

    relevant_pdf = (
        "https://example.gov.in/tenders/"
        "NIT_Structural_Consultancy.pdf"
    )

    html = f"""
    <html>
        <body>
            <h1>Notice Inviting Tender</h1>

            <a href="{relevant_pdf}">
                Download Tender Document
            </a>

            <a href="/annual-report-2025.pdf">
                Annual Report
            </a>
        </body>
    </html>
    """

    resolver = SourceResolver()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=page_url,
            text=html,
            content_type="text/html; charset=utf-8",
        )
    )

    result = resolver.resolve(page_url)

    results.append(
        run_test(
            "Relevant tender PDF selected",
            result == relevant_pdf,
        )
    )

    # ------------------------------------------------------------------
    # 3. HTML PAGE WITH ONLY IRRELEVANT PDF
    # ------------------------------------------------------------------

    irrelevant_page_url = (
        "https://example.gov.in/"
        "documents"
    )

    irrelevant_pdf = (
        "https://example.gov.in/documents/"
        "annual-report-2025.pdf"
    )

    irrelevant_html = f"""
    <html>
        <body>
            <h1>Publications</h1>

            <a href="{irrelevant_pdf}">
                Annual Report
            </a>
        </body>
    </html>
    """

    resolver = SourceResolver()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=irrelevant_page_url,
            text=irrelevant_html,
            content_type="text/html",
        )
    )

    result = resolver.resolve(
        irrelevant_page_url
    )

    results.append(
        run_test(
            "Irrelevant PDF not blindly selected",
            result == irrelevant_page_url,
        )
    )

    # ------------------------------------------------------------------
    # 4. REDIRECTED HTML PAGE
    # ------------------------------------------------------------------

    original_url = (
        "https://example.gov.in/"
        "tender-page"
    )

    redirected_url = (
        "https://example.gov.in/"
        "procurement/tender-page"
    )

    redirected_pdf = (
        "https://example.gov.in/"
        "procurement/RFP_structural_engineering.pdf"
    )

    redirected_html = f"""
    <html>
        <body>
            <h1>Request for Proposal</h1>

            <a href="{redirected_pdf}">
                RFP Tender Document
            </a>
        </body>
    </html>
    """

    resolver = SourceResolver()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=redirected_url,
            text=redirected_html,
            content_type="text/html",
        )
    )

    result = resolver.resolve(
        original_url
    )

    results.append(
        run_test(
            "Relevant PDF selected after redirect",
            result == redirected_pdf,
        )
    )

    # ------------------------------------------------------------------
    # 5. NETWORK FAILURE
    # ------------------------------------------------------------------

    failed_url = (
        "https://example.gov.in/"
        "unavailable-tender"
    )

    resolver = SourceResolver()

    resolver.session = FakeSession(
        exception=requests.RequestException(
            "Simulated network failure"
        )
    )

    result = resolver.resolve(
        failed_url
    )

    results.append(
        run_test(
            "Network failure falls back to original URL",
            result == failed_url,
        )
    )

    # ------------------------------------------------------------------
    # 6. URL FRAGMENT NORMALIZATION
    # ------------------------------------------------------------------

    fragment_url = (
        "https://example.gov.in/"
        "tenders/notice.pdf#section-1"
    )

    expected_url = (
        "https://example.gov.in/"
        "tenders/notice.pdf"
    )

    result = resolver.resolve(
        fragment_url
    )

    results.append(
        run_test(
            "PDF URL fragment removed",
            result == expected_url,
        )
    )

    # ------------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)

    if all(results):
        print("STATUS: PASS")
        print(
            "SourceResolver passed all focused "
            "behavioral checks."
        )
    else:
        print("STATUS: FAIL")
        print(
            "One or more SourceResolver checks failed."
        )

    print("=" * 80)


if __name__ == "__main__":
    main()