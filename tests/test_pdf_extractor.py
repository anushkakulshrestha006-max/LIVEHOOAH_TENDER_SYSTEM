from core.services.pdf_extractor import PDFExtractor


def test_is_useful_page_accepts_normal_tender_text():
    extractor = PDFExtractor()

    text = (
        "Notice Inviting Tender for structural consultancy services "
        "including design review and technical assessment."
    )

    assert extractor._is_useful_page(text) is True


def test_is_useful_page_rejects_low_value_content():
    extractor = PDFExtractor()

    assert extractor._is_useful_page("") is False
    assert extractor._is_useful_page("Tender notice") is False
    assert (
        extractor._is_useful_page(
            "Ref data 12345678901234567890123456789012345678901234567890"
        )
        is False
    )


def test_clean_text_normalizes_pdf_artifacts():
    extractor = PDFExtractor()

    text = (
        "  Notice   Inviting   Tender  \r\n"
        "\r\n"
        "\r\n"
        "Page 4 of 28\r\n"
        "\tScope   of   Work\t\r\n"
        "Structural   consultancy services\r\n"
    )

    assert extractor._clean_text(text) == (
        "Notice Inviting Tender\n\n"
        "Scope of Work\n"
        "Structural consultancy services"
    )


def test_repeated_header_on_minority_of_pages_is_preserved():
    extractor = PDFExtractor()

    pages = [
        "Scope of Work\nStructural design services for Tower A",
        "Scope of Work\nStructural design services for Tower B",
        "Eligibility Criteria\nConsultant must meet experience requirements",
        "Technical Bid\nSubmit technical proposal and credentials",
        "Financial Bid\nSubmit financial proposal separately",
    ]

    cleaned = extractor._remove_repeated_headers(pages)

    assert cleaned[0].startswith("Scope of Work\n")
    assert cleaned[1].startswith("Scope of Work\n")


def test_repeated_header_on_majority_of_pages_is_removed():
    extractor = PDFExtractor()

    pages = [
        "Government of India\nTender content for page one",
        "Government of India\nTender content for page two",
        "Government of India\nTender content for page three",
        "Eligibility Criteria\nTender content for page four",
        "Financial Bid\nTender content for page five",
    ]

    cleaned = extractor._remove_repeated_headers(pages)

    assert cleaned[0] == "Tender content for page one"
    assert cleaned[1] == "Tender content for page two"
    assert cleaned[2] == "Tender content for page three"


def test_repeated_footer_on_majority_of_pages_is_removed():
    extractor = PDFExtractor()

    pages = [
        "Scope of Work\nStructural consultancy services\nTender Reference ABC",
        "Eligibility Criteria\nMinimum experience required\nTender Reference ABC",
        "Technical Bid\nSubmit required documents\nDifferent Footer",
    ]

    cleaned = extractor._remove_repeated_headers(pages)

    assert cleaned[0] == "Scope of Work\nStructural consultancy services"
    assert cleaned[1] == "Eligibility Criteria\nMinimum experience required"
    assert cleaned[2].endswith("Different Footer")


def test_document_statistics_reports_basic_counts():
    extractor = PDFExtractor()

    stats = extractor.get_document_statistics(
        "Tender 123\nStructural consultancy"
    )

    assert stats == {
        "characters": 33,
        "words": 4,
        "lines": 2,
        "alphabetic": 27,
        "digits": 3,
    }


def test_repeated_header_on_exactly_half_of_pages_is_preserved():
    extractor = PDFExtractor()

    pages = [
        "Scope of Work\nStructural design services for Tower A",
        "Scope of Work\nStructural design services for Tower B",
        "Eligibility Criteria\nConsultant requirements",
        "Financial Bid\nCommercial proposal requirements",
    ]

    cleaned = extractor._remove_repeated_headers(pages)

    assert cleaned[0].startswith("Scope of Work\n")
    assert cleaned[1].startswith("Scope of Work\n")
