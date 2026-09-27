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
