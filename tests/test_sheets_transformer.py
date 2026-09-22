from sheets.sheets_transformer import (
    transform_opportunity,
    transform_opportunities,
    to_sheet_format
)


def test_transform_single_opportunity():

    opportunity = {
        "title": "Road Construction",
        "location": "Delhi",
        "value": "10 Cr",
        "deadline": "2026-07-01",
        "source": "GeM",
        "score": 0.91
    }

    result = transform_opportunity(opportunity)

    assert result["title"] == "Road Construction"
    assert result["priority"] == "HIGH"
    assert result["score"] == 0.91


def test_priority_medium():

    opportunity = {
        "title": "Bridge Project",
        "score": 0.60
    }

    result = transform_opportunity(opportunity)

    assert result["priority"] == "MEDIUM"


def test_priority_low():

    opportunity = {
        "title": "Drainage Work",
        "score": 0.30
    }

    result = transform_opportunity(opportunity)

    assert result["priority"] == "LOW"


def test_missing_fields():

    result = transform_opportunity({})

    assert result["title"] == ""
    assert result["location"] == ""
    assert result["score"] == 0

def test_transform_does_not_generate_opportunity_id():

    result = transform_opportunity({
        "title": "Structural Consultancy Tender",
        "score": 0.80
    })

    assert "opportunity_id" not in result


def test_transform_multiple():

    opportunities = [
        {"title": "A", "score": 0.9},
        {"title": "B", "score": 0.4}
    ]

    result = transform_opportunities(opportunities)

    assert len(result) == 2
    assert result[0]["priority"] == "HIGH"
    assert result[1]["priority"] == "LOW"



def test_source_url_preserved():

    opportunity = {
        "title": "Road Tender",
        "source_url": "https://gem.gov.in",
        "score": 0.8
    }

    result = transform_opportunity(opportunity)

    assert result["source_url"] == "https://gem.gov.in"

def test_qualification_reasoning_is_separate_from_matcher_reasoning():

    opportunity = {
        "title": "Structural Consultancy Tender",
        "score": 0.85,
        "reasoning": "MATCHER_REASONING",
        "qualification_reasoning": "QUALIFICATION_REASONING"
    }

    result = transform_opportunity(opportunity)

    assert result["reasoning"] == "MATCHER_REASONING"
    assert result["qualification_reasoning"] == "QUALIFICATION_REASONING"

def test_to_sheet_format_uses_qualification_reasoning():

    opportunity = {
        "opportunity_id": "OPP-TEST",
        "title": "Structural Consultancy Tender",
        "score": 0.85,
        "reasoning": "MATCHER_REASONING",
        "qualification_reasoning": "QUALIFICATION_REASONING"
    }

    result = to_sheet_format(opportunity)

    assert result["Qualification_Reasoning"] == "QUALIFICATION_REASONING"
    assert result["Qualification_Reasoning"] != "MATCHER_REASONING"
