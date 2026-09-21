from sheets.sheets_client import SheetsClient


def test_route_by_priority_high_boundary():

    client = SheetsClient.__new__(SheetsClient)

    assert client.route_by_priority({"score": 0.70}) == "HIGH"


def test_route_by_priority_medium_boundary():

    client = SheetsClient.__new__(SheetsClient)

    assert client.route_by_priority({"score": 0.50}) == "MEDIUM"


def test_route_by_priority_low_boundary():

    client = SheetsClient.__new__(SheetsClient)

    assert client.route_by_priority({"score": 0.49}) == "LOW"
