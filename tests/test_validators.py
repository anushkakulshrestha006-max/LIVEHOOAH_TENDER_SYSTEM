from utils.validators import (
    validate_title,
    validate_url,
    validate_email,
    validate_opportunity
)


def test_validate_title_accepts_valid_title():
    assert validate_title("Indian Army Tender") is True


def test_validate_title_rejects_short_title():
    assert validate_title("Test") is False


def test_validate_url_accepts_http_url():
    assert validate_url("https://gem.gov.in") is True


def test_validate_url_allows_empty_url():
    assert validate_url("") is True


def test_validate_url_rejects_invalid_url():
    assert validate_url("gem.gov.in") is False


def test_validate_email_accepts_valid_email():
    assert validate_email("test@example.com") is True


def test_validate_email_rejects_invalid_email():
    assert validate_email("invalid-email") is False


def test_validate_opportunity_accepts_valid_opportunity():
    assert validate_opportunity({
        "title": "Indian Army Tender",
        "source_url": "https://gem.gov.in"
    }) is True


def test_validate_opportunity_rejects_missing_source_url():
    assert validate_opportunity({
        "title": "Indian Army Tender"
    }) is False
