from sheets.sheets_transformer import (
    transform_opportunity,
    transform_opportunities
)


def test_transform_single_opportunity():

    opportunity = {
        "title": "Road Construction",
        "location": "Delhi",
        "value": "10 Cr",
        "deadline": "2026-07-01",
        "source": "GeM",
        "experience_score": 0.91
    }

    result = transform_opportunity(opportunity)

    assert result["title"] == "Road Construction"
    assert result["priority"] == "HIGH"
    assert result["score"] == 0.91


def test_priority_medium():

    opportunity = {
        "title": "Bridge Project",
        "experience_score": 0.60
    }

    result = transform_opportunity(opportunity)

    assert result["priority"] == "MEDIUM"


def test_priority_low():

    opportunity = {
        "title": "Drainage Work",
        "experience_score": 0.30
    }

    result = transform_opportunity(opportunity)

    assert result["priority"] == "LOW"


def test_missing_fields():

    result = transform_opportunity({})

    assert result["title"] == ""
    assert result["location"] == ""
    assert result["score"] == 0


def test_transform_multiple():

    opportunities = [
        {"title": "A", "experience_score": 0.9},
        {"title": "B", "experience_score": 0.4}
    ]

    result = transform_opportunities(opportunities)

    assert len(result) == 2
    assert result[0]["priority"] == "HIGH"
    assert result[1]["priority"] == "LOW"
    
    
    
def test_source_url_preserved():

    opportunity = {
        "title": "Road Tender",
        "source_url": "https://gem.gov.in",
        "experience_score": 0.8
    }

    result = transform_opportunity(opportunity)

    assert result["source_url"] == "https://gem.gov.in"