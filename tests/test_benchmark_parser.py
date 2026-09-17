from pathlib import Path

from core.services.pdf_extractor import PDFExtractor
from core.services.tender_parser import TenderParser


PDF_PATH = Path(
    "data/benchmark/pdfs/1499318164527_REQUEST_FOR_PROPOSAL.pdf"
)


def main():
    print("=" * 80)
    print("BENCHMARK PARSER TEST")
    print("=" * 80)

    if not PDF_PATH.exists():
        print("PDF NOT FOUND:", PDF_PATH)
        return

    pdf_bytes = PDF_PATH.read_bytes()

    print("PDF:", PDF_PATH)
    print("PDF SIZE:", len(pdf_bytes))

    # --------------------------------------------------------------
    # PDF EXTRACTION
    # --------------------------------------------------------------

    extractor = PDFExtractor()

    text = extractor.extract_text(pdf_bytes)

    print("\n" + "=" * 80)
    print("EXTRACTION STATISTICS")
    print("=" * 80)

    stats = extractor.get_document_statistics(text)

    for key, value in stats.items():
        print(f"{key:15}: {value}")

    print("\n" + "=" * 80)
    print("FIRST 150 LINES OF EXTRACTED TEXT")
    print("=" * 80)

    lines = text.splitlines()

    for index, line in enumerate(lines[:150], start=1):
        print(f"{index:04}: {line}")

    # --------------------------------------------------------------
    # TENDER PARSING
    # --------------------------------------------------------------

    parser = TenderParser()

    result = parser.parse(
        text,
        source_url=(
            "https://benchmark.local/"
            "1499318164527_REQUEST_FOR_PROPOSAL.pdf"
        ),
    )

    print("\n" + "=" * 80)
    print("TENDER PARSER RESULT")
    print("=" * 80)

    for key, value in result.items():
        print(f"{key:20}: {value}")

    print("=" * 80)


if __name__ == "__main__":
    main()