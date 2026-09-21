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
    assert len(client._opportunities_cache) == 2

    saved_record = client._opportunities_cache[-1]

    assert saved_record["Title"] == "New Structural Tender"
    assert saved_record["Source_Link"] == "https://example.com/new"
