import logging

from core.services.search_router import SearchRouter


logger = logging.getLogger(__name__)


# ==============================================================================
# LIVEHOOAH DISCOVERY CONFIGURATION
# ==============================================================================

# Keywords that indicate the query is already aligned with LiveHooah's business.
LIVEHOOAH_KEYWORDS = {
    "structural",
    "structure",
    "engineering",
    "consultant",
    "consultancy",
    "audit",
    "retrofitting",
    "retrofit",
    "rehabilitation",
    "proof",
    "peer",
    "review",
    "design",
    "building",
    "bridge",
    "industrial",
    "warehouse",
    "logistics",
    "steel",
    "peb",
    "rcc",
    "pmc",
    "authority",
    "inspection",
    "health",
    "assessment",
}


# Suffixes used to intelligently expand every base query.
SEARCH_SUFFIXES = (
    "",
    "tender",
    "RFP",
    "EOI",
    "empanelment",
    "consultancy services",
    "government tender",
    "eprocurement",
)


QUERY_PREFIX = "structural engineering consultancy"


# ==============================================================================
# LIVEHOOAH BASE DISCOVERY QUERIES
# ==============================================================================
# Keep these focused. Each query is expanded automatically by expand_query().
# Avoid adding contractor/supply/work-package style searches here.

LIVEHOOAH_QUERIES = [
    # ======================================================
    # CORE STRUCTURAL CONSULTANCY
    # ======================================================
    "structural consultant",
    "structural consultancy",
    "structural engineering consultancy",
    "structural consultant tender",
    "structural consultant empanelment",
    "structural consultant EOI",
    "structural consultant RFP",
    "appointment of structural consultant",
    "engineering consultancy structural",
    "civil structural consultant",

    # ======================================================
    # STRUCTURAL AUDIT / ASSESSMENT
    # ======================================================
    "structural audit",
    "structural safety audit",
    "structural inspection consultant",
    "building condition assessment",
    "structural health assessment",
    "existing building structural audit",
    "structural assessment consultant",

    # ======================================================
    # RETROFITTING / REHABILITATION
    # ======================================================
    "retrofitting consultancy",
    "structural rehabilitation",
    "repair rehabilitation consultancy",
    "building strengthening consultant",
    "retrofitting structural consultant",
    "rehabilitation structural consultant",

    # ======================================================
    # PROOF CHECKING / PEER REVIEW
    # ======================================================
    "proof checking consultant",
    "proof consultant",
    "peer review consultant",
    "structural proof checking",
    "independent proof consultant",
    "design verification consultant",

    # ======================================================
    # WAREHOUSE / INDUSTRIAL
    # ======================================================
    "warehouse structural consultant",
    "warehouse structural design",
    "industrial building consultancy",
    "industrial structural consultant",
    "industrial shed consultant",
    "logistics park structural consultant",
    "factory structural consultant",
    "PEB structural consultant",
    "steel structure consultant",

    # ======================================================
    # BUILDINGS
    # ======================================================
    "high rise structural consultant",
    "commercial building consultant",
    "residential tower structural consultant",
    "hospital structural consultant",
    "institutional building consultant",
    "government building consultant",

    # ======================================================
    # RELATED CONSULTANCY OPPORTUNITIES
    # ======================================================
    "project management consultancy building",
    "technical consultant civil",
    "engineering design consultant",
    "detailed engineering consultancy",
    "engineering consultancy services",

    # ======================================================
    # GOVERNMENT / URBAN OPPORTUNITIES
    # ======================================================
    "smart city engineering consultancy",
    
]

# Remove accidental duplicates while preserving order.
LIVEHOOAH_QUERIES = list(
    dict.fromkeys(
        LIVEHOOAH_QUERIES
    )
)


# ==============================================================================
# QUERY EXPANSION
# ==============================================================================

def expand_query(query: str):
    """
    Expand a single base query into multiple high-quality search variants.

    Example:

        structural audit

    becomes:

        structural audit
        structural audit tender
        structural audit RFP
        structural audit RFP PDF
        structural audit EOI
        structural audit EOI PDF
        structural audit empanelment
        structural audit consultancy services
        structural audit government tender
        structural audit eprocurement
    """

    expanded = []

    for suffix in SEARCH_SUFFIXES:

        if suffix:
            expanded.append(
                f"{query} {suffix}"
            )

        else:
            expanded.append(
                query
            )

        # Useful combinations for government procurement.
        if suffix in {"RFP", "EOI"}:

            expanded.append(
                f"{query} {suffix} PDF"
            )

    # Preserve ordering while removing duplicates.
    return list(
        dict.fromkeys(
            expanded
        )
    )


# ==============================================================================
# TENDER DISCOVERY PIPELINE
# ==============================================================================

def run_tender_discovery(query: str):
    """
    Run the discovery stage for a single base query.

    IMPORTANT
    ---------
    This function is responsible ONLY for discovery.

    It must NOT perform final:
        - document extraction
        - content deduplication
        - LiveHooah scoring
        - qualification
        - Google Sheets storage

    Those responsibilities belong to the downstream opportunity pipeline.

    Flow:

        Base Query
            ↓
        Query Expansion
            ↓
        SearchRouter
            ↓
        Raw Discovery Candidates
            ↓
        opportunity_pipeline.py

    Returns:

        {
            "status": "success",
            "opportunities": [...]
        }

    The returned opportunities are intentionally raw discovery candidates.
    """

    router = SearchRouter()

    expanded_queries = expand_query(
        query
    )

    logger.info(
        "Starting tender discovery | "
        "Base Query='%s' | "
        "Expanded Queries=%d",
        query,
        len(expanded_queries),
    )

    all_opportunities = []

    # ==========================================================================
    # SEARCH
    # ==========================================================================

    for search_query in expanded_queries:

        try:

            search_lower = search_query.lower()

            # If the query is already aligned with LiveHooah's business,
            # preserve it as-is. Otherwise prepend the core business context.
            if any(
                keyword in search_lower
                for keyword in LIVEHOOAH_KEYWORDS
            ):

                livehooah_query = search_query

            else:

                livehooah_query = (
                    f"{QUERY_PREFIX} "
                    f"{search_query}"
                )

            logger.info(
                "Searching | %s",
                livehooah_query,
            )

            opportunities = router.search(
                livehooah_query
            )

            if opportunities:

                logger.info(
                    "Search Complete | "
                    "Query='%s' | "
                    "Opportunities=%d",
                    livehooah_query,
                    len(opportunities),
                )

                all_opportunities.extend(
                    opportunities
                )

            else:

                logger.info(
                    "Search Complete | "
                    "Query='%s' | "
                    "Opportunities=0",
                    livehooah_query,
                )

        except Exception:

            logger.exception(
                "Search failed | Query='%s'",
                search_query,
            )

    logger.info(
        "Discovery Finished | "
        "Raw Opportunities=%d",
        len(all_opportunities),
    )

    # ==========================================================================
    # RETURN RAW DISCOVERY RESULTS
    # ==========================================================================

    return {
        "status": "success",
        "opportunities": all_opportunities,
    }