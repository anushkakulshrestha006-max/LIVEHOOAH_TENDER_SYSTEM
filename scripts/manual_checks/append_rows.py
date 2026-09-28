from sheets.sheets_client import SheetsClient

client = SheetsClient()

rows = [
    ["TEST_CATEGORY", "keyword_one", True],
    ["TEST_CATEGORY", "keyword_two", True]
]

client.append_rows(
    "Keywords",
    rows
)

print("Batch insert successful")