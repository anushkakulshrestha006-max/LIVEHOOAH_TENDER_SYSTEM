import time
import unicodedata
import gspread

from google.oauth2.service_account import Credentials
from datetime import datetime

from utils.id_generator import generate_id
from utils.validators import validate_opportunity
from utils.duplicate_detector import is_duplicate

from utils.logger import logger

from config.constants import (
    OPPORTUNITIES_SHEET,
    OPPORTUNITY_PREFIX,
    CONTACTS_SHEET,
    CONTACT_PREFIX,
    ACTIVITY_LOG_SHEET,
    CLIENT_WATCHLIST_SHEET,
    HIGH_PRIORITY_SHEET,
    MEDIUM_PRIORITY_SHEET,
    LOW_PRIORITY_SHEET
)


def retry_on_quota(func, retries=3, wait=15):
    for attempt in range(retries):
        try:
            return func()
        except gspread.exceptions.APIError as e:
            if "429" in str(e) and attempt < retries - 1:
                sleep_time = wait * (attempt + 1)
                print(f"\nRate limit hit. Waiting {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise
    return None


def clean_text(value):
    if not isinstance(value, str):
        return value if value is not None else ""
    try:
        fixed = value.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        fixed = value
    return unicodedata.normalize("NFKC", fixed)


class SheetsClient:

    def __init__(self):
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        self.creds = Credentials.from_service_account_file(
            "config/service_account.json",
            scopes=self.scopes
        )

        self.client = gspread.authorize(self.creds)

        self.sheet = self.client.open(
            "LIVEHOOAH Opportunity Intelligence Hub"
        )

        self._opportunities_cache = None

    def get_worksheet(self, name):
        return self.sheet.worksheet(name)

    def read_records(self, name):
        ws = self.get_worksheet(name)
        return retry_on_quota(lambda: ws.get_all_records())

    def _get_opportunities_cached(self):
        if self._opportunities_cache is None:
            self._opportunities_cache = self.read_records(
                OPPORTUNITIES_SHEET
            )
        return self._opportunities_cache

    def opportunity_exists(self, opportunity):

        records = self._get_opportunities_cached()

        logger.info("=" * 80)
        logger.info("Checking if opportunity already exists")
        logger.info(f"Cached records: {len(records)}")

        exists = is_duplicate(opportunity, records)

        logger.info(f"Duplicate Result: {exists}")

        return exists

    def generate_opportunity_id(self):
        records = self._get_opportunities_cached()
        return generate_id(OPPORTUNITY_PREFIX, len(records) + 1)

    def generate_contact_id(self):
        ws = self.get_worksheet(CONTACTS_SHEET)
        records = retry_on_quota(lambda: ws.get_all_records())
        return generate_id(CONTACT_PREFIX, len(records) + 1)

    def append_record(self, sheet_name, row):
        ws = self.get_worksheet(sheet_name)
        retry_on_quota(lambda: ws.append_row(row))

    def log_activity(self, agent, action, records_added, notes=""):
        ws = self.get_worksheet(ACTIVITY_LOG_SHEET)
        retry_on_quota(lambda: ws.append_row([
            datetime.utcnow().isoformat(),  # Timestamp
            agent,                           # Agent
            action,                          # Action
            records_added,                   # Records_Added
            notes                            # Notes
        ]))

    def get_priority_sheet(self, priority):
        if priority == "HIGH":
            return HIGH_PRIORITY_SHEET
        elif priority == "MEDIUM":
            return MEDIUM_PRIORITY_SHEET
        return LOW_PRIORITY_SHEET

    def route_by_priority(self, opportunity):
        score = float(opportunity.get("score", 0))
        if score >= 0.70:
            return "HIGH"
        elif score >= 0.50:
            return "MEDIUM"
        return "LOW"

    def save_opportunity(self, opportunity):

        if not validate_opportunity(opportunity):
            raise ValueError("Invalid opportunity data")

        if self.opportunity_exists(opportunity):

            logger.warning("=" * 80)
            logger.warning("SAVE ABORTED")
            logger.warning("Reason : Duplicate Opportunity")
            logger.warning(f"Title  : {opportunity.get('title', '')}")
            logger.warning(f"URL    : {opportunity.get('source_url', '')}")

            return {
               "status": "duplicate"
           }

    # Continue with the rest of your existing save logic below...

        score = float(opportunity.get("score", 0))

        

        opportunity_id = (
            opportunity.get("opportunity_id")
            or self.generate_opportunity_id()
            )

        if self._opportunities_cache is not None:
            self._opportunities_cache.append({})

        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        priority = self.route_by_priority(opportunity)

        # Build summary + why_selected combined text
        why_selected = opportunity.get("why_selected", [])
        if isinstance(why_selected, list):
            why_selected_text = "\n".join(why_selected)
        else:
            why_selected_text = str(why_selected)

        summary_text = clean_text(opportunity.get("summary", ""))

        if why_selected_text:
            summary_text += "\n\nWHY SELECTED:\n" + why_selected_text

        row = [
            opportunity_id,                                       # Opportunity_ID
            clean_text(opportunity.get("type", "")),              # Type
            clean_text(opportunity.get("title", "")),             # Title
            clean_text(opportunity.get("organization", "")),      # Organization
            clean_text(opportunity.get("service_category", "")),  # Service_Category
            clean_text(opportunity.get("location", "")),          # Location
            clean_text(opportunity.get("source", "")),            # Source
            opportunity.get("source_url", ""),                    # Source_Link
            clean_text(opportunity.get("deadline", "")),          # Deadline
            opportunity.get("contact_status", "NOT_CONTACTED"),   # Contact_Status
            opportunity.get("opportunity_status", "NEW"),         # Opportunity_Status
            priority,                                             # Priority
            score,                                                # Score
            opportunity.get("qualified", False),                  # Qualified
            opportunity.get("qualification_score", 0),            # Qualification_Score
            clean_text(
                opportunity.get("recommended_action", "")
            ),                                                    # Recommended_Action
            clean_text(
                opportunity.get("reasoning", "")
            ),                                                    # Qualification_Reasoning
            summary_text,                                         # Summary
            clean_text(
                opportunity.get("assigned_to", "")
            ),                                                    # Assigned_To
            now,                                                  # Last_Updated
            now                                                   # Date_Added
        ]
        
        logger.info("=" * 80)
        logger.info("GOOGLE SHEETS ROW")
        logger.info(f"Columns: {len(row)}")

        for i, value in enumerate(row, start=1):
            logger.info(f"{i}: {value}")
        self.append_record(OPPORTUNITIES_SHEET, row)
        if self._opportunities_cache is not None:
            self._opportunities_cache.append(
                {
                "Source_Link": opportunity.get(
                "source_url",
                ""
                )
                }
    )

        self.log_activity(
            agent="SYSTEM",
            action="OPPORTUNITY_CREATED",
            records_added=1,
            notes=(
                f"{opportunity_id} | "
                f"{opportunity.get('title','')} | "
                f"Score={score:.2f}"
            )
        )

        return {
            "status": "saved",
            "opportunity_id": opportunity_id
}

    def save_contact(self, contact):

        contact_id = self.generate_contact_id()
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            contact_id,                                        # Contact_ID
            clean_text(contact.get("organization", "")),       # Organization
            contact.get("opportunity_id", ""),                 # Opportunity_ID
            clean_text(contact.get("contact_name", "")),       # Contact_Name
            clean_text(contact.get("designation", "")),        # Designation
            contact.get("email", ""),                          # Email
            contact.get("phone", ""),                          # Phone
            contact.get("linkedin", ""),                       # LinkedIn
            clean_text(contact.get("source", "")),             # Source
            now                                                # Last_Updated
        ]

        self.append_record(CONTACTS_SHEET, row)

        self.log_activity(
            agent="SYSTEM",
            action="CONTACT_CREATED",
            records_added=1,
            notes=contact_id
        )

        return contact_id

    def update_watchlist(self, company, new_opportunity_title=""):

        ws = self.get_worksheet(CLIENT_WATCHLIST_SHEET)
        records = retry_on_quota(lambda: ws.get_all_records())

        for i, record in enumerate(records, start=2):
            if record.get("Company", "").lower() == company.lower():
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                retry_on_quota(lambda: ws.update_cell(i, 4, new_opportunity_title))
                retry_on_quota(lambda: ws.update_cell(i, 5, f"Auto-updated {now}"))
                return True

        return False