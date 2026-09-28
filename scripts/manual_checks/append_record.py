from sheets.sheets_client import SheetsClient

client = SheetsClient()

client.append_record(
    "Activity_Log",
    [
        "2026-06-11",
        "TEST_AGENT",
        "TEST_INSERT",
        1,
        "Connection test"
    ]
)

print("Row inserted successfully")