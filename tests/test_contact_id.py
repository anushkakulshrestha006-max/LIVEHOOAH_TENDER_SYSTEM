from sheets.sheets_client import SheetsClient

client = SheetsClient()

print(
    client.generate_contact_id()
)