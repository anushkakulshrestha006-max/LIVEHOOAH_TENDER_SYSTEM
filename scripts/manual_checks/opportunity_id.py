from sheets.sheets_client import SheetsClient

client = SheetsClient()

print(
    client.generate_opportunity_id()
)