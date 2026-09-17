from pathlib import Path

from core.services.tender_extraction_engine import (
    TenderExtractionEngine,
)


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
