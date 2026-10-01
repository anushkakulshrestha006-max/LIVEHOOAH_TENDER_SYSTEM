from core.services.tender_parser import TenderParser


def test_title_does_not_absorb_institutional_organization():
    parser = TenderParser()

    text = """
    NOTICE INVITING TENDER

    Empanelment of Structural Engineers for Consultancy Services

    INDIAN INSTITUTE OF TECHNOLOGY DELHI

    HAUZ KHAS, NEW DELHI

    Last Date: 15/09/2026
    """

    result = parser.parse(text)

    assert result["title"] == (
        "Empanelment of Structural Engineers for Consultancy Services"
    )
    assert result["organization"] == (
        "INDIAN INSTITUTE OF TECHNOLOGY DELHI"
    )


def test_location_does_not_extract_state_of_the_art():
    parser = TenderParser()

    text = """
    NOTICE INVITING TENDER

    Appointment of Structural Consultant for Laboratory Building

    The selected consultant will use state-of-the-art structural assessment techniques.

    Location: New Delhi

    Last Date: 15/09/2026
    """

    result = parser.parse(text)

    assert result["location"] == "New Delhi"


def test_location_extracts_explicit_state_label():
    parser = TenderParser()

    text = """
    NOTICE INVITING TENDER

    Appointment of Structural Consultant for Industrial Building

    State: Haryana

    Last Date: 15/09/2026
    """

    result = parser.parse(text)

    assert result["location"] == "Haryana"


def test_deadline_extracts_iso_date():
    parser = TenderParser()

    text = """
    NOTICE INVITING TENDER

    Appointment of Structural Consultant for Commercial Building

    Last Date: 2026-10-15
    """

    result = parser.parse(text)

    assert result["deadline"] == "2026-10-15"


def test_emd_extracts_plain_numeric_amount_after_explicit_label():
    parser = TenderParser()

    text = """
    NOTICE INVITING TENDER

    Structural Audit and Consultancy Services

    Last Date: 15/10/2026

    EMD: 175396
    """

    result = parser.parse(text)

    assert result["emd"] == "175396"


def test_document_fee_extracts_plain_numeric_amount_after_explicit_label():
    parser = TenderParser()

    text = """
    NOTICE INVITING TENDER

    Structural Audit and Consultancy Services

    Last Date: 15/10/2026

    Document Fee: 1500
    """

    result = parser.parse(text)

    assert result["document_fee"] == "1500"


REPRESENTATIVE_TENDER_TEXT = """NOTICE INVITING TENDER

1. Name of work : Consultancy Services for outsourcing Structural
Designs and Preparation of detailed estimate with
yard stick percentage, market rate analysis, draft
tenders as per MES format including tracing out
ambiguities in drgs if any wrt architectural,
structural and TD drgs for the building/structure for
“Provision of deficient single living accommodation for
Junior Sailors at Naval Base, Kochi.

2. Estimated Cost :

3. Period of Completion : 60 days from the date of placing supply/ job order.

4. Office : Chief Engineer (Naval Works) Kochi

5. Probable critical : As per details uploaded on web site
GeM Bid date schedule of quotation

SCOPE OF WORKS FOR STRUCTURAL DESIGN
Station : Kochi
Name of Work: Provn of deficient single living accommodation for Junior Sailors at Naval Base, Kochi

Technical reference to: E-in-C branch, New Delhi
"""


def test_title_extracts_work_name_and_excludes_subsequent_numbered_metadata():
    parser = TenderParser()
    result = parser.parse(REPRESENTATIVE_TENDER_TEXT)

    title = result["title"]
    assert title.startswith(
        "Consultancy Services for outsourcing Structural"
    ), f"Title did not start with work name description: {title!r}"
    assert "Estimated Cost" not in title, (
        f"Title absorbed subsequent metadata field: {title!r}"
    )
    assert title.endswith(
        "Junior Sailors at Naval Base, Kochi"
    ), f"Title did not capture full multiline work description: {title!r}"


def test_organization_extracts_labeled_office_and_rejects_title_continuation():
    parser = TenderParser()
    result = parser.parse(REPRESENTATIVE_TENDER_TEXT)

    assert result["organization"] == "Chief Engineer (Naval Works) Kochi", (
        f"Expected labeled office organization, got {result['organization']!r}"
    )


def test_location_prefers_labeled_station_over_incidental_technical_reference():
    parser = TenderParser()
    result = parser.parse(REPRESENTATIVE_TENDER_TEXT)

    assert result["location"] == "Kochi", (
        f"Expected labeled station location 'Kochi', got {result['location']!r}"
    )


def test_deadline_remains_empty_when_referenced_externally():
    parser = TenderParser()
    result = parser.parse(REPRESENTATIVE_TENDER_TEXT)

    assert result["deadline"] == "", (
        f"Expected empty deadline for external schedule, got {result['deadline']!r}"
    )
