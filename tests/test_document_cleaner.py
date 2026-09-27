from core.services.document_cleaner import DocumentCleaner


def test_clean_removes_common_web_noise_and_preserves_tender_content():
    cleaner = DocumentCleaner()

    text = """Home
Privacy Policy
We use cookies
Notice Inviting Tender
Structural consultancy services for building works
Scope of Work
Technical Bid
"""

    cleaned = cleaner.clean(text)

    assert "Home" not in cleaned
    assert "Privacy Policy" not in cleaned
    assert "We use cookies" not in cleaned

    assert "Notice Inviting Tender" in cleaned
    assert "Structural consultancy services for building works" in cleaned
    assert "Scope of Work" in cleaned
    assert "Technical Bid" in cleaned


def test_clean_rejects_obvious_error_page():
    cleaner = DocumentCleaner()

    text = """404
Page Not Found
The requested resource could not be located.
"""

    assert cleaner.clean(text) == ""


def test_clean_preserves_numbered_clause():
    cleaner = DocumentCleaner()

    text = """1. Scope of Work
Structural consultancy services
"""

    cleaned = cleaner.clean(text)

    assert "1. Scope of Work" in cleaned
    assert "Structural consultancy services" in cleaned


def test_clean_preserves_numeric_value_in_table_row():
    cleaner = DocumentCleaner()

    text = """Item | Amount
EMD | 175396
"""

    cleaned = cleaner.clean(text)

    assert "EMD | 175396" in cleaned


def test_clean_preserves_standalone_numeric_tender_value():
    cleaner = DocumentCleaner()

    text = """Earnest Money Deposit
175396
Technical Bid
"""

    cleaned = cleaner.clean(text)

    assert "Earnest Money Deposit" in cleaned
    assert "175396" in cleaned
    assert "Technical Bid" in cleaned
