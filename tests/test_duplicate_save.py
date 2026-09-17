from sheets.sheets_client import SheetsClient

client = SheetsClient()

opportunity = {
    "title": "Indian Army Drone Tender",
    "source_url": "https://gem.gov.in"
}

result = client.save_opportunity(opportunity)

print("RESULT:", result)