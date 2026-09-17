from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SERVICE_ACCOUNT_FILE = (
    BASE_DIR /
    "config" /
    "service_account.json"
)

GOOGLE_SHEET_NAME = (
    "LIVEHOOAH Opportunity Intelligence Hub"
)