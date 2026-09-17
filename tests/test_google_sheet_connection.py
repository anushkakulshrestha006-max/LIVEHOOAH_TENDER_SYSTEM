import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    "config/service_account.json",
    scopes=SCOPES
)

client = gspread.authorize(creds)

sheet = client.open("LIVEHOOAH Opportunity Intelligence Hub")

worksheet = sheet.worksheet("Opportunities")

records = worksheet.get_all_records()

print("✅ Connected successfully")
print(f"Rows found: {len(records)}")