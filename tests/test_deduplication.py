from core.services.deduplication import DeduplicationService


def test_duplicate_by_source_url():
    service = DeduplicationService()

    opportunities = [
        {
            "title": "Structural Consultancy Tender",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/123",
        },
        {
            "title": "Same Tender From Another Discovery Result",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/123",
        },
    ]

    result = service.deduplicate(opportunities)

    assert len(result) == 1


def test_duplicate_by_fingerprint():
    service = DeduplicationService()

    opportunities = [
        {
            "title": "Structural Consultancy Tender",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/123",
        },
        {
            "title": " STRUCTURAL CONSULTANCY TENDER ",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/456",
        },
    ]

    result = service.deduplicate(opportunities)

    assert len(result) == 1


def test_similar_title_same_organization_and_deadline_is_duplicate():
    service = DeduplicationService()

    opportunities = [
        {
            "title": "Structural Audit of Campus Buildings",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/123",
        },
        {
            "title": "Structural Audit of Campus Building",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/456",
        },
    ]

    result = service.deduplicate(opportunities)

    assert len(result) == 1


def test_similar_title_different_organization_is_preserved():
    service = DeduplicationService()

    opportunities = [
        {
            "title": "Structural Audit of Campus Buildings",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/123",
        },
        {
            "title": "Structural Audit of Campus Buildings",
            "organization": "IIT Bombay",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/456",
        },
    ]

    result = service.deduplicate(opportunities)

    assert len(result) == 2


def test_missing_metadata_is_preserved():
    service = DeduplicationService()

    opportunities = [
        {
            "title": "Structural Audit Tender",
            "organization": None,
            "deadline": None,
            "source_url": "https://example.com/1",
        },
        {
            "title": "Structural Audit Tender",
            "organization": None,
            "deadline": None,
            "source_url": "https://example.com/2",
        },
    ]

    result = service.deduplicate(opportunities)

    assert len(result) == 2


def test_same_title_and_organization_with_different_deadline_is_preserved():
    service = DeduplicationService()

    opportunities = [
        {
            "title": "Structural Audit of Campus Buildings",
            "organization": "IIT Delhi",
            "deadline": "2026-10-01",
            "source_url": "https://example.com/tender/123",
        },
        {
            "title": "Structural Audit of Campus Buildings",
            "organization": "IIT Delhi",
            "deadline": "2026-11-01",
            "source_url": "https://example.com/tender/456",
        },
    ]

    result = service.deduplicate(opportunities)

    assert len(result) == 2
