from sheets.sheets_client import SheetsClient

client = SheetsClient()

opportunity = {

    "title":
    "Indian Army Drone Tender",

    "source_url":
    "https://gem.gov.in",

    "organization":
    "Indian Army",

    "source":
    "GeM",

    "type":
    "Tender"
}

opportunity_id = (
    client.save_opportunity(
        opportunity
    )
)

print(
    f"Created: {opportunity_id}"
)