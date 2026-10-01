from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.services.tender_extraction_engine import (
    TenderExtractionEngine,
)


# ==============================================================================
# PYTEST SUITE: PUBLIC CONTRACT COVERAGE FOR TenderExtractionEngine.extract()
# ==============================================================================


def test_extract_html_success():
    engine = TenderExtractionEngine()

    raw_url = "https://example.com/portal/notice?id=101"
    resolved_url = "https://example.com/tenders/tender-101.html"
    assert resolved_url != raw_url

    engine.resolver = MagicMock()
    engine.resolver.resolve.return_value = resolved_url

    engine.fetcher = MagicMock()
    engine.fetcher.fetch.return_value = {
        "success": True,
        "content": "<html><body><h1>Tender Document</h1></body></html>",
        "content_type": "text/html",
    }

    html_text = (
        "Notice Inviting Tender for architectural and structural consultancy services. "
        "Detailed scope of work, technical bid qualification criteria, and submission requirements."
    )
    assert len(html_text) >= 120
    engine.html_extractor.extract_text = MagicMock(return_value=html_text)
    engine.cleaner.clean = MagicMock(side_effect=lambda text: text)

    mock_tender = {
        "title": "Architectural and Structural Consultancy Tender",
        "organization": "Public Works Department",
        "deadline": "2026-12-31",
        "location": "New Delhi",
    }
    engine.parser.parse = MagicMock(return_value=mock_tender)

    result = engine.extract(raw_url)

    assert isinstance(result, dict)
    assert result != {}
    assert result["source_url"] == resolved_url
    assert result["title"] == "Architectural and Structural Consultancy Tender"


def test_extract_pdf_routing_success():
    engine = TenderExtractionEngine()

    resolved_url = "https://example.com/documents/tender-202.pdf"
    engine.resolver = MagicMock()
    engine.resolver.resolve.return_value = resolved_url

    pdf_bytes = b"%PDF-1.4 simulated pdf stream"
    engine.fetcher = MagicMock()
    engine.fetcher.fetch.return_value = {
        "success": True,
        "content": pdf_bytes,
        "content_type": "application/pdf",
    }

    pdf_text = (
        "Request for proposal for empanelment of structural engineering consultants. "
        "Submissions must include technical bid documentation and comprehensive scope of work."
    )
    assert len(pdf_text) >= 120
    engine.pdf_extractor.extract_text = MagicMock(return_value=pdf_text)
    engine.html_extractor.extract_text = MagicMock()
    engine.cleaner.clean = MagicMock(side_effect=lambda text: text)

    mock_tender = {
        "title": "Empanelment of Structural Engineering Consultants RFP",
        "organization": "State Infrastructure Board",
        "deadline": "2026-11-30",
    }
    engine.parser.parse = MagicMock(return_value=mock_tender)

    result = engine.extract(resolved_url)

    assert isinstance(result, dict)
    assert result != {}
    assert result["title"] == "Empanelment of Structural Engineering Consultants RFP"
    assert result["source_url"] == resolved_url
    engine.pdf_extractor.extract_text.assert_called_once_with(pdf_bytes)
    engine.html_extractor.extract_text.assert_not_called()


@pytest.mark.parametrize(
    "raw_url,resolver_mock,fetcher_mock",
    [
        ("", None, None),
        ("   ", None, None),
        ("javascript:void(0)", None, None),
        (
            "https://example.com/tender",
            MagicMock(side_effect=RuntimeError("DNS resolution failed")),
            None,
        ),
        (
            "https://example.com/tender",
            MagicMock(return_value=""),
            None,
        ),
        (
            "https://example.com/tender",
            MagicMock(return_value="https://example.com/tender"),
            MagicMock(side_effect=ConnectionError("Fetch connection error")),
        ),
        (
            "https://example.com/tender",
            MagicMock(return_value="https://example.com/tender"),
            MagicMock(return_value={"success": False, "status_code": 404}),
        ),
        (
            "https://example.com/tender",
            MagicMock(return_value="https://example.com/tender"),
            MagicMock(return_value={"success": True, "content": ""}),
        ),
    ],
)
def test_extract_input_resolution_fetch_failures(raw_url, resolver_mock, fetcher_mock):
    engine = TenderExtractionEngine()
    if resolver_mock is not None:
        engine.resolver.resolve = resolver_mock
    if fetcher_mock is not None:
        engine.fetcher.fetch = fetcher_mock

    result = engine.extract(raw_url)

    assert result == {}


@pytest.mark.parametrize(
    "extractor_mock,cleaner_mock",
    [
        (MagicMock(side_effect=RuntimeError("Extraction crashed")), MagicMock()),
        (MagicMock(return_value=None), MagicMock()),
        (
            MagicMock(return_value="Extracted text that would otherwise be valid"),
            MagicMock(side_effect=RuntimeError("Cleaning crashed")),
        ),
        (
            MagicMock(return_value="Extracted text that would otherwise be valid"),
            MagicMock(return_value=12345),
        ),
    ],
)
def test_extract_extraction_cleaning_failures(extractor_mock, cleaner_mock):
    engine = TenderExtractionEngine()
    engine.resolver = MagicMock()
    engine.resolver.resolve.return_value = "https://example.com/tender.html"
    engine.fetcher = MagicMock()
    engine.fetcher.fetch.return_value = {
        "success": True,
        "content": "<html><body>Tender notice</body></html>",
        "content_type": "text/html",
    }
    engine.html_extractor.extract_text = extractor_mock
    engine.cleaner.clean = cleaner_mock

    result = engine.extract("https://example.com/tender.html")

    assert result == {}


@pytest.mark.parametrize(
    "invalid_text",
    [
        # Shorter than MIN_TEXT_LENGTH (120 characters)
        "Short tender notice for bid submission.",
        # Sufficiently long (>= 120 characters) with no tender signals
        (
            "Welcome to the annual community sports day and cultural festival. "
            "All neighborhood residents, families, and visitors are invited to attend "
            "the weekend activities including games, music, food stalls, and presentations."
        ),
    ],
)
def test_extract_document_validation_rejection(invalid_text):
    engine = TenderExtractionEngine()
    engine.resolver = MagicMock()
    engine.resolver.resolve.return_value = "https://example.com/notice.html"
    engine.fetcher = MagicMock()
    engine.fetcher.fetch.return_value = {
        "success": True,
        "content": "<html><body>content</body></html>",
        "content_type": "text/html",
    }
    engine.html_extractor.extract_text = MagicMock(return_value=invalid_text)
    engine.cleaner.clean = MagicMock(side_effect=lambda text: text)
    engine.parser.parse = MagicMock()

    result = engine.extract("https://example.com/notice.html")

    assert result == {}
    engine.parser.parse.assert_not_called()


def test_extract_rejects_garbled_text_with_tender_signals():
    engine = TenderExtractionEngine()

    engine.resolver = MagicMock()
    engine.resolver.resolve.return_value = (
        "https://example.com/noisy-page.html"
    )

    engine.fetcher = MagicMock()
    engine.fetcher.fetch.return_value = {
        "success": True,
        "content": "<html><body>content</body></html>",
        "content_type": "text/html",
    }

    garbled_text = (
        "x$#@!7]q{~|^%*&=+<>/\\ "
        "tender "
        "z]#@!{~^%*&=+<>/\\ "
        "request for proposal "
        "q$#@!7]{~|^%*&=+<>/\\ "
        "consultancy "
    ) * 40

    assert len(garbled_text) >= 120
    assert engine._document_score(garbled_text) >= 2

    engine.html_extractor.extract_text = MagicMock(
        return_value=garbled_text
    )
    engine.cleaner.clean = MagicMock(
        side_effect=lambda text: text
    )
    engine.parser.parse = MagicMock(
        return_value={
            "title": "Garbage Should Never Reach Parser",
        }
    )

    result = engine.extract(
        "https://example.com/noisy-page.html"
    )

    assert result == {}
    engine.parser.parse.assert_not_called()


def test_document_validation_accepts_symbol_heavy_tender_text():
    engine = TenderExtractionEngine()

    text = (
        "Notice Inviting Tender | RFP | Consultancy Services\n"
        "Tender No.: ABC/2026/17 | EMD: Rs. 50,000/-\n"
        "Scope of Work: Structural Audit & Assessment\n"
        "Technical Bid | Financial Bid | Submission: 31-12-2026\n"
        "Eligibility: Consultant / Engineer / Firm\n"
        + ("Structural consultancy services & tender submission. " * 8)
    )

    assert len(text) >= engine.MIN_TEXT_LENGTH
    assert engine._is_valid_document(
        text,
        "https://example.gov.in/tender/17",
    )


@pytest.mark.parametrize(
    "parser_result,parser_exc",
    [
        (None, RuntimeError("Parser internal error")),
        (["invalid", "result", "type"], None),
        ({}, None),
        ({"title": "Too short"}, None),
    ],
)
def test_extract_parser_structured_result_rejections(parser_result, parser_exc):
    engine = TenderExtractionEngine()
    engine.resolver = MagicMock()
    engine.resolver.resolve.return_value = "https://example.com/tender.html"
    engine.fetcher = MagicMock()
    engine.fetcher.fetch.return_value = {
        "success": True,
        "content": "<html><body>Tender notice</body></html>",
        "content_type": "text/html",
    }
    valid_text = (
        "Notice Inviting Tender for architectural and engineering consultancy services. "
        "Detailed scope of work, technical bid criteria, and submission instructions."
    )
    engine.html_extractor.extract_text = MagicMock(return_value=valid_text)
    engine.cleaner.clean = MagicMock(side_effect=lambda text: text)

    if parser_exc is not None:
        engine.parser.parse = MagicMock(side_effect=parser_exc)
    else:
        engine.parser.parse = MagicMock(return_value=parser_result)

    result = engine.extract("https://example.com/tender.html")

    assert result == {}


# ==============================================================================
# EXISTING BENCHMARK SCRIPT (PRESERVED UNCHANGED)
# ==============================================================================



PDF_PATH = Path(
    "data/benchmark/pdfs/1499318164527_REQUEST_FOR_PROPOSAL.pdf"
)

BENCHMARK_URL = (
    "https://benchmark.local/"
    "1499318164527_REQUEST_FOR_PROPOSAL.pdf"
)


class BenchmarkFetcher:
    """
    Test-only fetcher.

    Returns the real benchmark PDF through the same
    response contract expected from DocumentFetcher.

    No production code is modified.
    """

    def __init__(self, content: bytes):
        self.content = content

    def fetch(self, url: str) -> dict:
        return {
            "success": True,
            "content": self.content,
            "content_type": "application/pdf",
            "mime_type": "application/pdf",
            "content_hash": None,
            "content_size": len(self.content),
            "url": url,
            "final_url": url,
            "status_code": 200,
            "headers": {
                "Content-Type": "application/pdf",
            },
            "redirects": 0,
            "download_time": 0.0,
            "error": None,
            "error_type": None,
        }


def main():
    print("=" * 80)
    print("TENDER EXTRACTION ENGINE BENCHMARK TEST")
    print("=" * 80)

    if not PDF_PATH.exists():
        print("PDF NOT FOUND:", PDF_PATH)
        return

    pdf_bytes = PDF_PATH.read_bytes()

    print("PDF:", PDF_PATH)
    print("PDF SIZE:", len(pdf_bytes))

    engine = TenderExtractionEngine(
        save_benchmark_pdfs=False
    )

    engine.fetcher = BenchmarkFetcher(
        pdf_bytes
    )

    result = engine.extract(
        BENCHMARK_URL
    )

    print("\n" + "=" * 80)
    print("EXTRACTION ENGINE RESULT")
    print("=" * 80)

    print("RESULT TYPE:", type(result).__name__)
    print("RESULT EMPTY:", not bool(result))

    for key, value in result.items():
        print(f"{key:20}: {value}")

    print("\n" + "=" * 80)
    print("BENCHMARK VALIDATION")
    print("=" * 80)

    if not result:
        print("STATUS: FAILED")
        print("Reason: Extraction engine returned an empty result.")
        return

    expected_title = (
        "Empanelment of Structural Engineers for consultancy services"
    )

    expected_organization = "STATE BANK OF INDIA"
    expected_deadline = "2017-07-27"
    expected_location = "Navi Mumbai"
    expected_tender_type = "EMPANELMENT"

    checks = {
        "title": result.get("title") == expected_title,
        "organization": (
            result.get("organization")
            == expected_organization
        ),
        "deadline": (
            result.get("deadline")
            == expected_deadline
        ),
        "location": (
            result.get("location")
            == expected_location
        ),
        "tender_type": (
            result.get("tender_type")
            == expected_tender_type
        ),
        "description": bool(
            result.get("description")
        ),
        "source_url": (
            result.get("source_url")
            == BENCHMARK_URL
        ),
    }

    for key, passed in checks.items():
        print(
            f"{key:20}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print("\n" + "=" * 80)

    if all(checks.values()):
        print("STATUS: PASS")
        print(
            "TenderExtractionEngine successfully processed "
            "the benchmark PDF."
        )
    else:
        print("STATUS: FAIL")
        print(
            "One or more extraction-engine benchmark checks failed."
        )

    print("=" * 80)


if __name__ == "__main__":
    main()
