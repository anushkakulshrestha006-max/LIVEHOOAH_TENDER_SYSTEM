from core.services.opportunity_pipeline import qualify_opportunity


def valid_opportunity():
    return {
        "title": "Notice Inviting Tender for Structural Consultancy",
        "organization": "Central Public Works Department",
        "source_url": "https://example.gov.in/tender/101",
        "deadline": "2099-12-31",
        "description": "Structural consultancy services for building works.",
        "score": 0.80,
    }


def test_qualify_valid_opportunity():
    qualified, reasons = qualify_opportunity(valid_opportunity())

    assert qualified is True
    assert reasons == ["Passed qualification"]


def test_qualify_rejects_invalid_tender():
    opportunity = valid_opportunity()
    opportunity["organization"] = ""

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Invalid or low-quality tender document" in reasons


def test_qualify_rejects_short_title():
    opportunity = valid_opportunity()
    opportunity["title"] = "Short"

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Title too short" in reasons


def test_qualify_rejects_missing_source_url():
    opportunity = valid_opportunity()
    opportunity["source_url"] = ""

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Missing source URL" in reasons


def test_qualify_rejects_expired_tender():
    opportunity = valid_opportunity()
    opportunity["deadline"] = "2020-01-01"

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Expired tender" in reasons


def test_qualify_rejects_reference_document():
    opportunity = valid_opportunity()
    opportunity["title"] = "Application for Empanelment of Structural Consultants"

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Reference/application document, not an active opportunity" in reasons


def test_qualify_rejects_without_active_opportunity_signal():
    opportunity = valid_opportunity()
    opportunity["title"] = "Structural Engineering Assessment"
    opportunity["description"] = "General information about structural engineering."

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "No clear active opportunity signal" in reasons


def test_qualify_rejects_score_below_threshold():
    opportunity = valid_opportunity()
    opportunity["score"] = 0.59

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Score below minimum LiveHooah threshold (0.59 < 0.60)" in reasons


def test_qualify_accepts_exact_minimum_score():
    opportunity = valid_opportunity()
    opportunity["score"] = 0.60

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is True
    assert reasons == ["Passed qualification"]


def test_qualify_accumulates_multiple_failure_reasons():
    opportunity = valid_opportunity()
    opportunity["title"] = "Short"
    opportunity["source_url"] = ""
    opportunity["score"] = 0.59

    qualified, reasons = qualify_opportunity(opportunity)

    assert qualified is False
    assert "Title too short" in reasons
    assert "Missing source URL" in reasons
    assert "Score below minimum LiveHooah threshold (0.59 < 0.60)" in reasons
