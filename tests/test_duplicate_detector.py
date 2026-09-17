from utils.duplicate_detector import is_duplicate


def test_duplicate_found():

    opportunity = {
        "title": "Road Tender",
        "source_url": "https://gem.gov.in/123"
    }

    existing = [
        {
            "Title": "Road Tender",
            "Source_Link": "https://gem.gov.in/123"
        }
    ]

    assert is_duplicate(
        opportunity,
        existing
    ) is True


def test_duplicate_not_found():

    opportunity = {
        "title": "Road Tender",
        "source_url": "https://gem.gov.in/123"
    }

    existing = [
        {
            "Title": "Bridge Tender",
            "Source_Link": "https://gem.gov.in/999"
        }
    ]

    assert is_duplicate(
        opportunity,
        existing
    ) is False


def test_case_insensitive():

    opportunity = {
        "title": "ROAD TENDER",
        "source_url": "HTTPS://GEM.GOV.IN/123"
    }

    existing = [
        {
            "Title": "road tender",
            "Source_Link": "https://gem.gov.in/123"
        }
    ]

    assert is_duplicate(
        opportunity,
        existing
    ) is True