import time
import uuid
from datetime import datetime

from utils.logger import logger
from core.services.deduplication import DeduplicationService
from agents.tender_discovery_agent import (
    run_tender_discovery,
    LIVEHOOAH_QUERIES,
)
from sheets.sheets_transformer import transform_opportunities
from sheets.sheets_client import SheetsClient
from core.services.tender_extraction_engine import TenderExtractionEngine
from core.scoring.livehooah_matcher import compute_livehooah_score


engine = TenderExtractionEngine()
deduplicator = DeduplicationService()

MIN_LIVEHOOAH_SCORE = 0.60


# =====================================================
# FINAL GARBAGE FILTER
# =====================================================

def is_valid_tender(op):

    title = (
        op.get("title") or ""
    ).strip()

    org = (
        op.get("organization") or ""
    ).strip()

    title_lower = title.lower()

    generic_titles = {
        "request for proposal",
        "rfp",
        "tender",
        "expression of interest",
        "document for eoi",
        "application form",
        "tender document",
        "bid document",
    }

    if title_lower in generic_titles:

        return False

    junk_pages = [
        "home page",
        "sign in",
        "login",
        "privacy policy",
        "cookie",
    ]

    if any(
        junk in title_lower
        for junk in junk_pages
    ):

        return False

    if not org:

        return False

    return True


# =====================================================
# DATE HELPERS
# =====================================================

def parse_deadline(deadline):

    if not deadline:

        return None

    if hasattr(
        deadline,
        "date",
    ):

        try:

            return deadline.date()

        except Exception:

            pass

    deadline = str(
        deadline
    ).strip()

    formats = (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
    )

    for fmt in formats:

        try:

            return datetime.strptime(
                deadline,
                fmt,
            ).date()

        except ValueError:

            continue

    return None


def is_expired(opportunity):

    deadline = parse_deadline(
        opportunity.get(
            "deadline"
        )
    )

    if not deadline:

        return False

    return deadline < datetime.today().date()


# =====================================================
# REFERENCE / NON-OPPORTUNITY DOCUMENT FILTER
# =====================================================

def is_reference_document(opportunity):

    title = (
        opportunity.get("title") or ""
    ).strip().lower()

    description = (
        opportunity.get("description") or ""
    ).strip().lower()

    combined_text = (
        f"{title} {description}"
    )

    reference_patterns = [

        "application form",

        "application for empanelment",

        "application for registration",

        "registration form",

        "enrolment form",

        "enrollment form",

        "list of empanelled consultants",

        "list of empaneled consultants",

        "list of approved consultants",

        "building safety certificate",

        "certificate of structural safety",

        "format for application",

        "form for application",

    ]

    for pattern in reference_patterns:

        if pattern in combined_text:

            return True

    return False


# =====================================================
# ACTIVE OPPORTUNITY SIGNAL
# =====================================================

def has_active_opportunity_signal(opportunity):

    title = (
        opportunity.get("title") or ""
    ).lower()

    description = (
        opportunity.get("description") or ""
    ).lower()

    combined_text = (
        f"{title} {description}"
    )

    active_signals = [

        # General active tender signals
        "notice inviting tender",

        "invites applications",

        "invitation for bids",

        "request for proposal",

        "request for quotation",

        "expression of interest",

        "eoi",

        "empanelment of",

        "selection of consultant",

        "selection of consultants",

        "appointment of consultant",

        "appointment of consultants",

        "consultancy services",

        "tender for",

        "bid for",

        "invitation to tender",

        # Structural consultancy-specific active signals
        "appointment of structural consultant",

        "appointment of structural consultants",

        "selection of structural consultant",

        "selection of structural consultants",

        "engagement of structural consultant",

        "engagement of structural consultants",

        "invitation for structural consultant",

        "invitation for structural consultants",

        "empanelment of structural consultant",

        "empanelment of structural consultants",

    ]
    return any(
        signal in combined_text
        for signal in active_signals
    )


# =====================================================
# QUALIFICATION
# =====================================================

def qualify_opportunity(opportunity):

    """
    Decide whether an opportunity should move to storage.

    Relevance scoring and qualification are separate:

        SCORE
            ↓
        Is this relevant to Livehooah?

        QUALIFICATION
            ↓
        Is this an active, usable opportunity?

    Returns:
        (qualified: bool, reasons: list)
    """

    reasons = []

    score = float(
        opportunity.get(
            "score",
            0,
        )
    )

    title = (
        opportunity.get("title") or ""
    ).strip()

    source_url = (
        opportunity.get(
            "source_url",
            "",
        )
        or ""
    ).strip()

    # -------------------------------------------------
    # BASIC DATA VALIDATION
    # -------------------------------------------------

    if not is_valid_tender(
        opportunity
    ):

        reasons.append(
            "Invalid or low-quality tender document"
        )

    if len(title) < 15:

        reasons.append(
            "Title too short"
        )

    if not source_url:

        reasons.append(
            "Missing source URL"
        )

    # -------------------------------------------------
    # EXPIRED OPPORTUNITY CHECK
    # -------------------------------------------------

    if is_expired(
        opportunity
    ):

        reasons.append(
            "Expired tender"
        )

    # -------------------------------------------------
    # REFERENCE DOCUMENT CHECK
    # -------------------------------------------------

    if is_reference_document(
        opportunity
    ):

        reasons.append(
            "Reference/application document, not an active opportunity"
        )

    # -------------------------------------------------
    # ACTIVE OPPORTUNITY SIGNAL
    # -------------------------------------------------

    if not has_active_opportunity_signal(
        opportunity
    ):

        reasons.append(
            "No clear active opportunity signal"
        )

    # -------------------------------------------------
    # LIVEHOOAH RELEVANCE SCORE
    # -------------------------------------------------

    if score < MIN_LIVEHOOAH_SCORE:

        reasons.append(
            f"Score below minimum LiveHooah threshold ({score:.2f} < {MIN_LIVEHOOAH_SCORE:.2f})"
        )

    # -------------------------------------------------
    # FINAL DECISION
    # -------------------------------------------------

    if reasons:

        return False, reasons

    return True, [
        "Passed qualification"
    ]


# =====================================================
# MAIN PIPELINE
# =====================================================

def run_pipeline(
    query: str,
    max_retries: int = 3,
):

    logger.info(
        "=" * 80
    )

    logger.info(
        f"Starting pipeline for query: {query}"
    )

    result = {
        "opportunities": []
    }

    last_result = None

    # =================================================
    # RETRY LAYER
    # =================================================

    for attempt in range(
        max_retries
    ):

        try:

            result = run_tender_discovery(
                query
            )

        except Exception as e:

            logger.error(
                f"Discovery crash on attempt "
                f"{attempt + 1}: {e}"
            )

            result = {
                "opportunities": []
            }

        opportunities = result.get(
            "opportunities",
            []
        )

        if opportunities:

            last_result = result

            break

        logger.warning(
            f"Empty discovery result. "
            f"Retry {attempt + 1}/{max_retries}"
        )

        time.sleep(
            2 * (
                attempt + 1
            )
        )

    if not last_result:

        return {
            "meta": {
                "query": query,
                "total_found": 0,
                "saved": 0,
                "duplicates": 0,
                "failed": 0,
                "note": "Discovery failed",
            },
            "opportunities": [],
        }

    raw_opportunities = last_result.get(
        "opportunities",
        []
    )

    # =================================================
    # STEP 1: URL DEDUPLICATION
    # =================================================

    seen = set()

    deduped = []

    for opp in raw_opportunities:

        url = opp.get(
            "source_url"
        )

        if not url:

            continue

        if url in seen:

            continue

        seen.add(
            url
        )

        deduped.append(
            opp
        )

    # =================================================
    # STEP 2: EXTRACTION
    # =================================================

    structured = []

    failed = 0

    for opp in deduped:

        url = opp.get(
            "source_url"
        )

        try:

            extracted = engine.extract(
                url
            )

            if (
                extracted
                and extracted.get(
                    "title"
                )
            ):

                structured.append(
                    extracted
                )

            else:

                logger.warning(
                    "Extraction returned no usable "
                    "structured tender | %s",
                    url,
                )

                failed += 1

        except Exception:

            logger.exception(
                "Extraction failed unexpectedly | %s",
                url,
            )

            failed += 1

    if not structured:

        return {
            "meta": {
                "query": query,
                "total_found": 0,
                "saved": 0,
                "duplicates": 0,
                "failed": failed,
                "note": "No structured tenders",
            },
            "opportunities": [],
        }

    # =================================================
    # STEP 3: CONTENT DEDUPLICATION
    # =================================================

    structured = deduplicator.deduplicate(
        structured
    )

    # =================================================
    # STEP 4: SCORING + QUALIFICATION
    # =================================================

    qualified = []

    for opp in structured:

        score, reasons = compute_livehooah_score(
            opp
        )

        opp["score"] = score

        opp["reasoning"] = (
            " | ".join(
                reasons
            )
        )

        qualified_flag, qualification_reasons = (
            qualify_opportunity(
                opp
            )
        )

        opp["qualification_status"] = (

            "QUALIFIED"

            if qualified_flag

            else "REJECTED"

        )

        opp["qualification_reasoning"] = (
            " | ".join(
                qualification_reasons
            )
        )

        if not qualified_flag:

            logger.info(
                f"REJECTED | "
                f"{opp.get('title', '')} | "
                f"{opp['qualification_reasoning']}"
            )

            continue

        qualified.append(
            opp
        )

        logger.info(
            f"QUALIFIED | "
            f"Score={score:.2f} | "
            f"{opp.get('title', '')}"
        )

    # =================================================
    # STEP 5: TRANSFORM
    # =================================================

    transformed = transform_opportunities(
        qualified
    )

    sheets_client = SheetsClient()

    saved = 0

    duplicates = 0

    # =================================================
    # STEP 6: SAVE TO SHEETS
    # =================================================

    for opportunity in transformed:

        logger.info(
            "-" * 80
        )

        logger.info(
            "Preparing opportunity for Google Sheets"
        )

        logger.info(
            f"Title                : "
            f"{opportunity.get('title')}"
        )

        logger.info(
            f"Qualification Status : "
            f"{opportunity.get('qualification_status')}"
        )

        logger.info(
            f"Opportunity ID       : "
            f"{opportunity.get('opportunity_id')}"
        )

        logger.info(
            f"Score                : "
            f"{opportunity.get('score')}"
        )

        if (
            opportunity.get(
                "qualification_status"
            )
            != "QUALIFIED"
        ):

            logger.warning(
                f"SKIPPED -> "
                f"qualification_status = "
                f"{opportunity.get('qualification_status')}"
            )

            continue

        if not opportunity.get(
            "opportunity_id"
        ):

            opportunity[
                "opportunity_id"
            ] = str(
                uuid.uuid4()
            )

        logger.info(
            "Calling SheetsClient.save_opportunity()..."
        )

        try:

            result = (
                sheets_client.save_opportunity(
                    opportunity
                )
            )

            logger.info(
                f"SheetsClient returned: "
                f"{result}"
            )

            if not result:

                failed += 1

                logger.warning(
                    "SheetsClient returned no result"
                )

                continue

            status = result.get(
                "status"
            )

            if status == "saved":

                saved += 1

                logger.info(
                    "Opportunity SAVED successfully"
                )

            elif status == "duplicate":

                duplicates += 1

                logger.warning(
                    "Duplicate opportunity - "
                    "not saved"
                )

            elif status == "failed":

                failed += 1

                logger.warning(
                    "SheetsClient reported failure"
                )

            else:

                failed += 1

                logger.warning(
                    f"Unknown SheetsClient status: "
                    f"{status}"
                )

        except Exception:

            failed += 1

            logger.exception(
                "Google Sheets write failed"
            )

    logger.info(
        f"Pipeline Complete | "
        f"Query={query} | "
        f"Qualified={len(qualified)} | "
        f"Saved={saved} | "
        f"Duplicates={duplicates} | "
        f"Failed={failed}"
    )

    return {
        "meta": {
            "query": query,
            "total_found": len(
                qualified
            ),
            "saved": saved,
            "duplicates": duplicates,
            "failed": failed,
        },
        "opportunities": transformed,
    }


# =====================================================
# BATCH PIPELINE
# =====================================================

def run_livehooah_pipeline():

    all_opportunities = []

    stats = {
        "total_queries": len(
            LIVEHOOAH_QUERIES
        ),
        "total_found": 0,
        "total_saved": 0,
        "total_duplicates": 0,
        "total_failed": 0,
    }

    for query in LIVEHOOAH_QUERIES:

        result = run_pipeline(
            query
        )

        all_opportunities.extend(
            result.get(
                "opportunities",
                []
            )
        )

        meta = result.get(
            "meta",
            {}
        )

        stats[
            "total_found"
        ] += meta.get(
            "total_found",
            0
        )

        stats[
            "total_saved"
        ] += meta.get(
            "saved",
            0
        )

        stats[
            "total_duplicates"
        ] += meta.get(
            "duplicates",
            0
        )

        stats[
            "total_failed"
        ] += meta.get(
            "failed",
            0
        )

    return {
        "meta": stats,
        "opportunities": all_opportunities,
    }