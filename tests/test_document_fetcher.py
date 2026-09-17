from dataclasses import dataclass

import requests

from core.services.document_fetcher import DocumentFetcher


# ============================================================================
# TEST-ONLY FAKE RESPONSE
# ============================================================================


@dataclass
class FakeResponse:
    """
    Minimal test-only replacement for requests.Response.
    """

    url: str
    content: bytes
    content_type: str = "application/pdf"
    status_code: int = 200
    history: list = None

    def __post_init__(self):
        self.headers = {
            "Content-Type": self.content_type,
        }

        if self.history is None:
            self.history = []

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(
                f"HTTP {self.status_code}"
            )

            error.response = self

            raise error

    def iter_content(self, chunk_size=8192):
        for index in range(
            0,
            len(self.content),
            chunk_size,
        ):
            yield self.content[
                index:index + chunk_size
            ]

    def close(self):
        pass


# ============================================================================
# TEST-ONLY FAKE SESSION
# ============================================================================


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
        self.max_redirects = 10

    def get(
        self,
        url,
        timeout=None,
        allow_redirects=True,
        stream=True,
    ):
        if self.exception:
            raise self.exception

        return self.response

    def close(self):
        pass


# ============================================================================
# TEST HELPERS
# ============================================================================


def run_test(
    name,
    condition,
):
    status = "PASS" if condition else "FAIL"

    print(
        f"{name:55}: {status}"
    )

    return condition


def create_pdf_content():
    """
    Create a minimal PDF-like byte sequence.

    The DocumentFetcher only needs the %PDF magic bytes
    for MIME detection in this test.
    """

    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog >>\n"
        b"endobj\n"
        b"%%EOF"
    )


def create_html_content():
    """
    Create minimal HTML content.
    """

    return (
        b"<!DOCTYPE html>"
        b"<html>"
        b"<head><title>Tender</title></head>"
        b"<body>"
        b"<h1>Notice Inviting Tender</h1>"
        b"</body>"
        b"</html>"
    )


# ============================================================================
# MAIN TEST
# ============================================================================


def main():
    print("=" * 80)
    print("DOCUMENT FETCHER TEST")
    print("=" * 80)

    results = []

    # ------------------------------------------------------------------
    # 1. SUCCESSFUL PDF DOWNLOAD
    # ------------------------------------------------------------------

    pdf_url = (
        "https://example.gov.in/"
        "tenders/structural-tender.pdf"
    )

    pdf_content = create_pdf_content()

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=pdf_url,
            content=pdf_content,
            content_type="application/pdf",
        )
    )

    result = resolver.fetch(pdf_url)

    results.append(
        run_test(
            "Successful PDF download",
            (
                result["success"] is True
                and result["content"] == pdf_content
                and result["mime_type"]
                == "application/pdf"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 2. PDF CONTENT HASH
    # ------------------------------------------------------------------

    expected_hash = (
        resolver._calculate_sha256(
            pdf_content
        )
    )

    results.append(
        run_test(
            "SHA-256 content hash generated",
            result["content_hash"]
            == expected_hash,
        )
    )

    # ------------------------------------------------------------------
    # 3. PDF CONTENT SIZE
    # ------------------------------------------------------------------

    results.append(
        run_test(
            "Content size reported correctly",
            result["content_size"]
            == len(pdf_content),
        )
    )

    # ------------------------------------------------------------------
    # 4. PDF CONTENT TYPE
    # ------------------------------------------------------------------

    results.append(
        run_test(
            "PDF MIME type detected correctly",
            result["content_type"]
            == "application/pdf"
            and result["mime_type"]
            == "application/pdf",
        )
    )

    # ------------------------------------------------------------------
    # 5. SOURCE URL AND FINAL URL
    # ------------------------------------------------------------------

    results.append(
        run_test(
            "Source and final URLs preserved",
            (
                result["url"] == pdf_url
                and result["final_url"]
                == pdf_url
            ),
        )
    )

    # ------------------------------------------------------------------
    # 6. SUCCESS RESPONSE CONTRACT
    # ------------------------------------------------------------------

    expected_success_keys = {
        "success",
        "content",
        "content_type",
        "mime_type",
        "content_hash",
        "content_size",
        "url",
        "final_url",
        "status_code",
        "headers",
        "redirects",
        "download_time",
        "error",
        "error_type",
    }

    results.append(
        run_test(
            "Success response contract preserved",
            expected_success_keys.issubset(
                result.keys()
            ),
        )
    )

    # ------------------------------------------------------------------
    # 7. HTML DOWNLOAD
    # ------------------------------------------------------------------

    html_url = (
        "https://example.gov.in/"
        "tenders/structural-tender"
    )

    html_content = create_html_content()

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=html_url,
            content=html_content,
            content_type="text/html; charset=utf-8",
        )
    )

    result = resolver.fetch(html_url)

    results.append(
        run_test(
            "Successful HTML download",
            (
                result["success"] is True
                and result["content"]
                == html_content
                and result["mime_type"]
                == "text/html"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 8. EMPTY URL
    # ------------------------------------------------------------------

    resolver = DocumentFetcher()

    result = resolver.fetch("")

    results.append(
        run_test(
            "Empty URL rejected",
            (
                result["success"] is False
                and result["error_type"]
                == "invalid_url"
                and result["content"] is None
            ),
        )
    )

    # ------------------------------------------------------------------
    # 9. BLANK URL
    # ------------------------------------------------------------------

    result = resolver.fetch(
        "   "
    )

    results.append(
        run_test(
            "Blank URL rejected",
            (
                result["success"] is False
                and result["error_type"]
                == "invalid_url"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 10. NETWORK FAILURE
    # ------------------------------------------------------------------

    failed_url = (
        "https://example.gov.in/"
        "unavailable.pdf"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        exception=requests.exceptions.ConnectionError(
            "Simulated connection failure"
        )
    )

    result = resolver.fetch(
        failed_url
    )

    results.append(
        run_test(
            "Network failure classified correctly",
            (
                result["success"] is False
                and result["error_type"]
                == "connection_error"
                and result["content"] is None
            ),
        )
    )

    # ------------------------------------------------------------------
    # 11. CONNECT TIMEOUT
    # ------------------------------------------------------------------

    timeout_url = (
        "https://example.gov.in/"
        "timeout.pdf"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        exception=requests.exceptions.ConnectTimeout(
            "Simulated connect timeout"
        )
    )

    result = resolver.fetch(
        timeout_url
    )

    results.append(
        run_test(
            "Connect timeout classified correctly",
            (
                result["success"] is False
                and result["error_type"]
                == "connect_timeout"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 12. HTTP ERROR
    # ------------------------------------------------------------------

    http_error_url = (
        "https://example.gov.in/"
        "missing.pdf"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=http_error_url,
            content=b"",
            content_type="text/html",
            status_code=404,
        )
    )

    result = resolver.fetch(
        http_error_url
    )

    results.append(
        run_test(
            "HTTP error classified correctly",
            (
                result["success"] is False
                and result["error_type"]
                == "http_404"
                and result["status_code"]
                == 404
            ),
        )
    )

    # ------------------------------------------------------------------
    # 13. EMPTY RESPONSE
    # ------------------------------------------------------------------

    empty_url = (
        "https://example.gov.in/"
        "empty.pdf"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=empty_url,
            content=b"",
            content_type="application/pdf",
        )
    )

    result = resolver.fetch(
        empty_url
    )

    results.append(
        run_test(
            "Empty response rejected",
            (
                result["success"] is False
                and result["error_type"]
                == "empty_response"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 14. FAKE PDF CONTAINING HTML
    # ------------------------------------------------------------------

    fake_pdf_url = (
        "https://example.gov.in/"
        "fake.pdf"
    )

    fake_pdf_content = create_html_content()

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=fake_pdf_url,
            content=fake_pdf_content,
            content_type="application/pdf",
        )
    )

    result = resolver.fetch(
        fake_pdf_url
    )

    results.append(
        run_test(
            "Fake PDF containing HTML rejected",
            (
                result["success"] is False
                and result["error_type"]
                == "fake_pdf_html"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 15. INVALID PDF
    # ------------------------------------------------------------------

    invalid_pdf_url = (
        "https://example.gov.in/"
        "invalid.pdf"
    )

    invalid_pdf_content = (
        b"This is not a real PDF document."
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=invalid_pdf_url,
            content=invalid_pdf_content,
            content_type="application/pdf",
        )
    )

    result = resolver.fetch(
        invalid_pdf_url
    )

    results.append(
        run_test(
            "Invalid PDF content rejected",
            (
                result["success"] is False
                and result["error_type"]
                == "invalid_pdf"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 16. UNSUPPORTED CONTENT TYPE
    # ------------------------------------------------------------------

    image_url = (
        "https://example.gov.in/"
        "image.jpg"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=image_url,
            content=b"\xff\xd8\xff\xe0"
            + b"image-data",
            content_type="image/jpeg",
        )
    )

    result = resolver.fetch(
        image_url
    )

    results.append(
        run_test(
            "Unsupported image content rejected",
            (
                result["success"] is False
                and result["error_type"]
                == "unsupported_content_type"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 17. LOGIN PAGE DETECTION
    # ------------------------------------------------------------------

    login_url = (
        "https://example.gov.in/"
        "secure-tender"
    )

    login_content = (
        b"<!DOCTYPE html>"
        b"<html>"
        b"<body>"
        b"<h1>Sign In</h1>"
        b"<p>Please enter your password.</p>"
        b"</body>"
        b"</html>"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=login_url,
            content=login_content,
            content_type="text/html",
        )
    )

    result = resolver.fetch(
        login_url
    )

    results.append(
        run_test(
            "Login page detected",
            (
                result["success"] is False
                and result["error_type"]
                == "login_required"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 18. CAPTCHA DETECTION
    # ------------------------------------------------------------------

    captcha_url = (
        "https://example.gov.in/"
        "protected-tender"
    )

    captcha_content = (
        b"<!DOCTYPE html>"
        b"<html>"
        b"<body>"
        b"<h1>Security Check</h1>"
        b"<p>Verify you are human.</p>"
        b"</body>"
        b"</html>"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=captcha_url,
            content=captcha_content,
            content_type="text/html",
        )
    )

    result = resolver.fetch(
        captcha_url
    )

    results.append(
        run_test(
            "CAPTCHA page detected",
            (
                result["success"] is False
                and result["error_type"]
                == "captcha"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 19. DOWNLOAD SIZE ENFORCEMENT
    # ------------------------------------------------------------------

    large_url = (
        "https://example.gov.in/"
        "large-tender.pdf"
    )

    large_content = (
        b"%PDF-1.4\n"
        + b"A" * 100
    )

    resolver = DocumentFetcher(
        max_download_size=50
    )

    resolver.session = FakeSession(
        response=FakeResponse(
            url=large_url,
            content=large_content,
            content_type="application/pdf",
        )
    )

    result = resolver.fetch(
        large_url
    )

    results.append(
        run_test(
            "Maximum download size enforced",
            (
                result["success"] is False
                and result["error_type"]
                == "content_too_large"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 20. CONTENT-LENGTH SIZE ENFORCEMENT
    # ------------------------------------------------------------------

    declared_large_url = (
        "https://example.gov.in/"
        "declared-large.pdf"
    )

    response = FakeResponse(
        url=declared_large_url,
        content=b"%PDF-1.4",
        content_type="application/pdf",
    )

    response.headers["Content-Length"] = "1000"

    resolver = DocumentFetcher(
        max_download_size=100
    )

    resolver.session = FakeSession(
        response=response
    )

    result = resolver.fetch(
        declared_large_url
    )

    results.append(
        run_test(
            "Declared content size enforced",
            (
                result["success"] is False
                and result["error_type"]
                == "content_too_large"
            ),
        )
    )

    # ------------------------------------------------------------------
    # 21. REDIRECT INFORMATION
    # ------------------------------------------------------------------

    redirected_url = (
        "https://example.gov.in/"
        "procurement/final-tender.pdf"
    )

    original_redirect_url = (
        "https://example.gov.in/"
        "tender.pdf"
    )

    fake_redirect = object()

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=redirected_url,
            content=pdf_content,
            content_type="application/pdf",
            history=[
                fake_redirect,
            ],
        )
    )

    result = resolver.fetch(
        original_redirect_url
    )

    results.append(
        run_test(
            "Redirect count reported correctly",
            (
                result["success"] is True
                and result["redirects"] == 1
                and result["url"]
                == original_redirect_url
                and result["final_url"]
                == redirected_url
            ),
        )
    )

    # ------------------------------------------------------------------
    # 22. OCTET-STREAM PDF DETECTION
    # ------------------------------------------------------------------

    octet_stream_url = (
        "https://example.gov.in/"
        "download"
    )

    resolver = DocumentFetcher()

    resolver.session = FakeSession(
        response=FakeResponse(
            url=octet_stream_url,
            content=pdf_content,
            content_type="application/octet-stream",
        )
    )

    result = resolver.fetch(
        octet_stream_url
    )

    results.append(
        run_test(
            "PDF detected despite octet-stream MIME",
            (
                result["success"] is True
                and result["mime_type"]
                == "application/pdf"
            ),
        )
    )

    # ------------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)

    passed = sum(
        1
        for result in results
        if result
    )

    total = len(results)

    print(
        f"PASSED: {passed}/{total}"
    )

    if all(results):
        print("STATUS: PASS")
        print(
            "DocumentFetcher passed all focused "
            "offline behavioral checks."
        )
    else:
        print("STATUS: FAIL")
        print(
            "One or more DocumentFetcher checks failed."
        )

    print("=" * 80)


if __name__ == "__main__":
    main()