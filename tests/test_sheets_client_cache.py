from sheets.sheets_client import SheetsClient


def test_save_opportunity_updates_cache_with_saved_record_once(monkeypatch):

    client = SheetsClient.__new__(SheetsClient)

    client._opportunities_cache = [
        {
            "Title": "Existing Tender",
            "Source_Link": "https://example.com/existing"
        }
    ]

    opportunity = {
        "title": "New Structural Tender",
        "source_url": "https://example.com/new"
    }

    monkeypatch.setattr(
        client,
        "opportunity_exists",
        lambda opportunity: False
    )

    monkeypatch.setattr(
        client,
        "generate_opportunity_id",
        lambda: "OPP-000002"
    )

    monkeypatch.setattr(
        client,
        "append_record",
        lambda sheet_name, row: None
    )

    monkeypatch.setattr(
        client,
        "log_activity",
        lambda **kwargs: None
    )

    result = client.save_opportunity(opportunity)

    assert result["status"] == "saved"
    assert result["opportunity_id"] == "OPP-000002"
    assert len(client._opportunities_cache) == 2

    saved_record = client._opportunities_cache[-1]

    assert saved_record["Title"] == "New Structural Tender"
    assert saved_record["Source_Link"] == "https://example.com/new"

def test_save_opportunity_rejects_invalid_opportunity():

    client = SheetsClient.__new__(SheetsClient)

    opportunity = {
        "title": "Valid Tender"
    }

    try:
        client.save_opportunity(opportunity)
        assert False, "Expected ValueError for invalid opportunity"
    except ValueError as exc:
        assert str(exc) == "Invalid opportunity data"


def test_save_opportunity_rejects_duplicate_without_persisting(monkeypatch):

    client = SheetsClient.__new__(SheetsClient)

    client._opportunities_cache = []

    opportunity = {
        "title": "Duplicate Structural Tender",
        "source_url": "https://example.com/duplicate"
    }

    monkeypatch.setattr(
        client,
        "opportunity_exists",
        lambda opportunity: True
    )

    def fail_append(*args, **kwargs):
        raise AssertionError("append_record must not be called for duplicates")

    monkeypatch.setattr(client, "append_record", fail_append)

    monkeypatch.setattr(
        client,
        "log_activity",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("log_activity must not be called for duplicates")
        )
    )

    result = client.save_opportunity(opportunity)

    assert result == {"status": "duplicate"}
    assert client._opportunities_cache == []


def test_save_opportunity_persists_qualification_fields(monkeypatch):

    client = SheetsClient.__new__(SheetsClient)

    client._opportunities_cache = []

    opportunity = {
        "title": "Structural Consultancy Tender",
        "source_url": "https://example.com/tender",
        "score": 0.85,
        "qualification_score": 0.78,
        "recommended_action": "PURSUE",
        "qualification_reasoning": "Qualified structural consultancy opportunity"
    }

    monkeypatch.setattr(
        client,
        "opportunity_exists",
        lambda opportunity: False
    )

    monkeypatch.setattr(
        client,
        "generate_opportunity_id",
        lambda: "OPP-000001"
    )

    captured = {}

    def capture_append(sheet_name, row):
        captured["sheet_name"] = sheet_name
        captured["row"] = row

    monkeypatch.setattr(client, "append_record", capture_append)
    monkeypatch.setattr(
        client,
        "log_activity",
        lambda **kwargs: None
    )

    result = client.save_opportunity(opportunity)

    assert result["status"] == "saved"
    assert captured["row"][14] == 0.78
    assert captured["row"][15] == "PURSUE"
    assert captured["row"][16] == "Qualified structural consultancy opportunity"


def test_save_opportunity_preserves_supplied_opportunity_id(monkeypatch):

    client = SheetsClient.__new__(SheetsClient)

    client._opportunities_cache = []

    opportunity = {
        "opportunity_id": "OPP-000123",
        "title": "Structural Consultancy Tender",
        "source_url": "https://example.com/supplied-id",
        "score": 0.80,
    }

    monkeypatch.setattr(
        client,
        "opportunity_exists",
        lambda opportunity: False
    )

    def fail_generate():
        raise AssertionError(
            "generate_opportunity_id must not be called when an ID is supplied"
        )

    monkeypatch.setattr(
        client,
        "generate_opportunity_id",
        fail_generate
    )

    captured = {}

    def capture_append(sheet_name, row):
        captured["sheet_name"] = sheet_name
        captured["row"] = row

    monkeypatch.setattr(client, "append_record", capture_append)

    monkeypatch.setattr(
        client,
        "log_activity",
        lambda **kwargs: None
    )

    result = client.save_opportunity(opportunity)

    assert result == {
        "status": "saved",
        "opportunity_id": "OPP-000123",
    }

    assert captured["row"][0] == "OPP-000123"
