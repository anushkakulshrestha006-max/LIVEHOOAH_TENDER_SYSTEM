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
