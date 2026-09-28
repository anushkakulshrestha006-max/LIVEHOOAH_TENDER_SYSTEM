from sheets.sheets_client import SheetsClient

client = SheetsClient()

client.log_activity(
    agent="SYSTEM",
    action="TEST_LOG",
    records_added=1,
    notes="Step 4.6 validation"
)

print("Activity log created successfully")