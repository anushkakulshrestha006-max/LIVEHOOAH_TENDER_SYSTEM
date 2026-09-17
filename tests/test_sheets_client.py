from sheets.sheets_client import SheetsClient

client = SheetsClient()

records = client.read_records("Opportunities")

print(records)