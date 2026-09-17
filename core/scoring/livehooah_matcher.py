import re
from datetime import date, datetime

from config.livehooah_keywords import LIVEHOOAH_KEYWORDS


# ==========================================================
# CONFIGURATION
# ==========================================================

# --------------------------------------------------------------------------
# Core LiveHooah capabilities
# --------------------------------------------------------------------------
#
# These are the strongest indicators of an opportunity matching
# LiveHooah's structural engineering consultancy business.
#
# IMPORTANT:
# This is a relevance scorer only.
# Qualification / pursuit decisions happen later.
# --------------------------------------------------------------------------

LIVEHOOAH_CORE = {
    "structural engineering": 0.20,
    "structural consultancy": 0.25,
    "structural design": 0.20,
    "structural analysis": 0.18,
    "proof checking": 0.22,
    "peer review": 0.18,
    "structural audit": 0.20,
    "retrofit": 0.18,
    "retrofitting": 0.18,
    "rehabilitation": 0.18,
    "structural health monitoring": 0.20,

    # Building / industrial segments
    "warehouse": 0.12,
    "logistics park": 0.12,
    "fulfillment center": 0.12,
    "industrial building": 0.12,
    "industrial shed": 0.10,
    "high rise": 0.10,
    "high-rise": 0.10,
    "commercial tower": 0.12,
    "residential tower": 0.10,

    # Structural systems
    "rcc": 0.08,
    "steel structure": 0.10,
    "pre engineered building": 0.10,
    "pre-engineered building": 0.10,
    "peb": 0.08,
}


# --------------------------------------------------------------------------
# Secondary relevance signals
# --------------------------------------------------------------------------

SECONDARY_MATCHES = {
    "industrial": 0.05,
    "commercial": 0.05,
    "structural": 0.08,
    "warehouse": 0.05,
    "building": 0.04,
    "tower": 0.04,
    "logistics": 0.05,
}


# --------------------------------------------------------------------------
# Actual procurement / opportunity signals
# --------------------------------------------------------------------------

REAL_OPPORTUNITY_TERMS = [
    "tender",
    "rfp",
    "request for proposal",
    "expression of interest",
    "eoi",
    "bid",
    "empanelment",
    "consultancy services",
    "notice inviting tender",
    "invitation for bids",
    "invitation to tender",
    "selection of consultant",
    "selection of consultants",
    "appointment of consultant",
    "appointment of consultants",
]


# --------------------------------------------------------------------------
# Strong LiveHooah service signals
# --------------------------------------------------------------------------

LIVEHOOAH_OPPORTUNITY_TERMS = [
    "structural consultant",
    "structural consultancy",
    "structural engineering consultancy",
    "structural design consultancy",
    "structural engineer",
    "structural engineering",
    "proof checking",
    "structural audit",
    "peer review",
    "retrofit",
    "retrofitting",
    "rehabilitation",
    "design and drawings",
    "architectural and structural",
    "structural assessment",
    "structural inspection",
    "structural safety audit",
    "building condition assessment",
    "structural health assessment",
    "design verification",
]


# --------------------------------------------------------------------------
# Preferred regions
# --------------------------------------------------------------------------
#
# Positive boost for locations that are particularly useful for LiveHooah.
# --------------------------------------------------------------------------

REGION_BOOST = {
    "delhi": 0.10,
    "new delhi": 0.10,
    "ncr": 0.10,
    "noida": 0.10,
    "greater noida": 0.10,
    "ghaziabad": 0.10,
    "gurgaon": 0.10,
    "gurugram": 0.10,
    "faridabad": 0.08,
    "uttar pradesh": 0.05,
    "haryana": 0.05,
}


# --------------------------------------------------------------------------
# Regions that should receive a mild penalty when the opportunity is
# outside LiveHooah's preferred operating geography.
#
# This is deliberately a penalty, not a hard exclusion.
# A highly relevant structural consultancy tender outside NCR should still
# remain discoverable.
# --------------------------------------------------------------------------

NON_PREFERRED_REGION_PENALTY = {
    "kerala": 0.06,
    "tamil nadu": 0.05,
    "andhra pradesh": 0.05,
    "telangana": 0.05,
    "karnataka": 0.05,
    "maharashtra": 0.04,
    "gujarat": 0.04,
    "rajasthan": 0.03,
    "west bengal": 0.04,
    "odisha": 0.04,
    "assam": 0.05,
    "bihar": 0.04,
    "jharkhand": 0.04,
    "chhattisgarh": 0.04,
    "madhya pradesh": 0.04,
    "punjab": 0.03,
    "uttarakhand": 0.03,
    "goa": 0.04,
    "jammu and kashmir": 0.05,
    "ladakh": 0.05,
}


# --------------------------------------------------------------------------
# Negative signals
# --------------------------------------------------------------------------
#
# These do not automatically reject an opportunity.
# They reduce relevance because these terms commonly indicate work outside
# LiveHooah's core structural consultancy scope.
# --------------------------------------------------------------------------

NEGATIVE_KEYWORDS = {
    "road": 0.05,
    "roads": 0.05,
    "bridge": 0.03,
    "bridges": 0.03,
    "highway": 0.08,
    "highways": 0.08,
    "expressway": 0.08,
    "greenfield corridor": 0.08,
    "railway": 0.05,
    "airport": 0.04,
    "electrical maintenance": 0.12,
    "housekeeping": 0.20,
    "sanitation": 0.20,
    "sweeping": 0.20,
    "survey only": 0.15,
    "dpr only": 0.15,
    "manpower supply": 0.20,
    "security services": 0.20,
    "vehicle hiring": 0.20,
    "transportation services": 0.20,
    "catering services": 0.20,
}


# --------------------------------------------------------------------------
# Preferred organizations
# --------------------------------------------------------------------------

PREFERRED_ORGANIZATIONS = {
    "cpwd": 0.06,
    "nbcc": 0.06,
    "dmrc": 0.06,
    "iit": 0.05,
    "aiims": 0.05,
    "municipal corporation": 0.04,
    "smart city": 0.04,
    "development authority": 0.04,
}


# --------------------------------------------------------------------------
# Official source bonuses
# --------------------------------------------------------------------------

OFFICIAL_SOURCES = {
    "etenders.gov.in": 0.05,
    "gem.gov.in": 0.05,
    "eprocure.gov.in": 0.05,
    "gov.in": 0.03,
}


# --------------------------------------------------------------------------
# Title-specific relevance signals
# --------------------------------------------------------------------------

TITLE_IMPORTANT_TERMS = [
    "consultant",
    "consultancy",
    "structural",
    "proof checking",
    "empanelment",
    "rfp",
    "eoi",
    "retrofit",
    "retrofitting",
    "audit",
    "peer review",
    "structural engineering",
    "structural design",
    "structural assessment",
]


# ==========================================================
# TEXT MATCHING HELPERS
# ==========================================================

def _contains_keyword(text: str, keyword: str) -> bool:
    """
    Safely match a keyword or phrase as a complete textual term.

    Prevents substring false positives such as:

        blocked keyword: "port"
        document text:   "report"

    while still supporting multi-word phrases such as:

        "structural design"
        "proof checking"
        "greenfield corridor"
    """

    text = str(text or "").lower()
    keyword = str(keyword or "").strip().lower()

    if not text or not keyword:
        return False

    pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"

    return bool(re.search(pattern, text))


def _count_keyword_matches(
    text: str,
    keywords,
) -> list:
    """
    Return all keywords that appear as complete textual terms.
    """

    return [
        keyword
        for keyword in keywords
        if _contains_keyword(text, keyword)
    ]


# ==========================================================
# DATE HELPERS
# ==========================================================

def parse_deadline(deadline):
    """
    Convert supported deadline values into a date object.

    Supports:
        - datetime
        - date
        - YYYY-MM-DD
        - DD-MM-YYYY
        - DD/MM/YYYY
    """

    if not deadline:
        return None

    if isinstance(deadline, datetime):
        return deadline.date()

    if isinstance(deadline, date):
        return deadline

    deadline = str(deadline).strip()

    if not deadline:
        return None

    formats = (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
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


# ==========================================================
# FRESHNESS
# ==========================================================

def freshness_score(deadline):

    deadline = parse_deadline(deadline)

    if not deadline:

        return (
            0.02,
            "Deadline missing",
        )

    days = (
        deadline
        - datetime.today().date()
    ).days

    if days < 0:

        return (
            0.00,
            "Expired tender",
        )

    if days <= 7:

        return (
            0.08,
            "Closing within 7 days",
        )

    if days <= 30:

        return (
            0.12,
            "Active tender",
        )

    return (
        0.15,
        "Fresh opportunity",
    )


# ==========================================================
# METADATA COMPLETENESS
# ==========================================================

def metadata_score(opportunity):

    fields = [
        "title",
        "organization",
        "deadline",
        "location",
        "description",
        "contact_email",
        "contact_phone",
        "source",
    ]

    filled = sum(
        bool(
            str(
                opportunity.get(
                    field,
                    "",
                )
            ).strip()
        )
        for field in fields
    )

    score = min(
        filled * 0.015,
        0.12,
    )

    return (
        score,
        f"{filled}/{len(fields)} metadata fields populated",
    )


# ==========================================================
# LOCATION SCORING
# ==========================================================

def apply_region_score(
    text: str,
    reasons: list,
):
    """
    Apply one geographic signal.

    Preferred region gets a positive boost.

    Non-preferred region gets a mild penalty.

    We deliberately stop after the first matched region so that a tender
    mentioning several locations does not receive multiple geographic
    bonuses/penalties.
    """

    for region, weight in REGION_BOOST.items():

        if _contains_keyword(
            text,
            region,
        ):

            reasons.append(
                f"Preferred region ({region})"
            )

            return weight

    for region, penalty in NON_PREFERRED_REGION_PENALTY.items():

        if _contains_keyword(
            text,
            region,
        ):

            reasons.append(
                f"Non-preferred region ({region}) "
                f"(-{round(penalty, 2)})"
            )

            return -penalty

    return 0.0


# ==========================================================
# MAIN SCORING
# ==========================================================

def compute_livehooah_score(opportunity):

    """
    Calculate LiveHooah business relevance.

    IMPORTANT ARCHITECTURAL CONTRACT
    --------------------------------
    This function is the canonical business relevance scorer.

    It does NOT:
        - perform discovery
        - fetch documents
        - parse documents
        - call GPT
        - save to Google Sheets
        - decide final pursuit status

    It only calculates:

        opportunity
            ↓
        relevance score + reasons

    Returns:
        (float score, list[str] reasons)
    """

    # ======================================================
    # BUILD SEARCHABLE TEXT
    # ======================================================

    text = " ".join(
        [
            str(
                opportunity.get(
                    "title",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "description",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "summary",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "location",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "organization",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "source",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "source_url",
                    "",
                )
            ),
        ]
    ).lower()

    score = 0.0

    reasons = []

    # ======================================================
    # HARD BLOCKED KEYWORDS
    # ======================================================

    blocked = [
        str(keyword).lower().strip()
        for keyword in LIVEHOOAH_KEYWORDS.get(
            "blocked",
            [],
        )
        if str(keyword).strip()
    ]

    for keyword in blocked:

        if _contains_keyword(
            text,
            keyword,
        ):

            return (
                0.0,
                [
                    f"Blocked keyword: {keyword}"
                ],
            )

    # ======================================================
    # CORE CAPABILITY SCORE
    # ======================================================

    core_hits = []

    for keyword, weight in LIVEHOOAH_CORE.items():

        if _contains_keyword(
            text,
            keyword,
        ):

            core_hits.append(
                keyword
            )

            score += weight

    # Prevent a document containing many overlapping variants
    # from receiving an excessive core score.
    #
    # The strongest evidence is retained, while repetitive terms
    # such as "structural", "structural engineering", "structural
    # design", etc. cannot inflate the score indefinitely.

    if core_hits:

        core_cap = 0.55

        if score > core_cap:

            score = core_cap

        reasons.append(
            f"{len(core_hits)} core capability matches"
        )

    else:

        fallback = [
            keyword
            for keyword in SECONDARY_MATCHES
            if _contains_keyword(
                text,
                keyword,
            )
        ]

        if not fallback:

            return (
                0.0,
                [
                    "No structural relevance detected"
                ],
            )

        for keyword in fallback:

            score += SECONDARY_MATCHES[
                keyword
            ]

        reasons.append(
            "Weak structural relevance "
            "(secondary fallback)"
        )

    # ======================================================
    # TENDER OPPORTUNITY SIGNAL
    # ======================================================

    tender_hits = _count_keyword_matches(
        text,
        REAL_OPPORTUNITY_TERMS,
    )

    if tender_hits:

        # Opportunity signal is important, but capped.
        score += 0.20

        reasons.append(
            "Tender opportunity detected "
            f"({len(tender_hits)} signal(s))"
        )

    else:

        # A technically relevant document without procurement
        # language is less useful as an actual opportunity.
        score *= 0.80

        reasons.append(
            "Weak tender signal"
        )

    # ======================================================
    # LIVEHOOAH SERVICE SIGNAL
    # ======================================================

    service_hits = _count_keyword_matches(
        text,
        LIVEHOOAH_OPPORTUNITY_TERMS,
    )

    if service_hits:

        bonus = min(
            len(service_hits) * 0.04,
            0.20,
        )

        score += bonus

        reasons.append(
            "Relevant consultancy service "
            f"({len(service_hits)} match(es))"
        )

    else:

        score *= 0.90

        reasons.append(
            "Weak consultancy relevance"
        )

    # ======================================================
    # REGION
    # ======================================================

    score += apply_region_score(
        text,
        reasons,
    )

    # ======================================================
    # ORGANIZATION QUALITY
    # ======================================================

    organization = str(
        opportunity.get(
            "organization",
            "",
        )
    ).lower()

    for org, weight in PREFERRED_ORGANIZATIONS.items():

        if _contains_keyword(
            organization,
            org,
        ):

            score += weight

            reasons.append(
                f"Preferred organization ({org})"
            )

            break

    # ======================================================
    # SOURCE QUALITY
    # ======================================================

    source = " ".join(
        [
            str(
                opportunity.get(
                    "source",
                    "",
                )
            ),
            str(
                opportunity.get(
                    "source_url",
                    "",
                )
            ),
        ]
    ).lower()

    for source_domain, weight in OFFICIAL_SOURCES.items():

        if _contains_keyword(
            source,
            source_domain,
        ):

            score += weight

            reasons.append(
                f"Official source ({source_domain})"
            )

            break

    # ======================================================
    # DEADLINE / FRESHNESS
    # ======================================================

    fresh_score, fresh_reason = freshness_score(
        opportunity.get(
            "deadline"
        )
    )

    score += fresh_score

    reasons.append(
        fresh_reason
    )

    # ======================================================
    # METADATA COMPLETENESS
    # ======================================================

    meta_score, meta_reason = metadata_score(
        opportunity
    )

    score += meta_score

    reasons.append(
        meta_reason
    )

    # ======================================================
    # NEGATIVE SIGNALS
    # ======================================================

    total_penalty = 0.0

    negative_found = []

    for keyword, penalty in NEGATIVE_KEYWORDS.items():

        if _contains_keyword(
            text,
            keyword,
        ):

            total_penalty += penalty

            negative_found.append(
                keyword
            )

    if total_penalty:

        total_penalty = min(
            total_penalty,
            0.30,
        )

        score -= total_penalty

        reasons.append(
            "Negative keywords: "
            f"{', '.join(negative_found)} "
            f"(-{round(total_penalty, 2)})"
        )

    # ======================================================
    # TITLE RELEVANCE
    # ======================================================

    title = str(
        opportunity.get(
            "title",
            "",
        )
    ).lower()

    title_hits = sum(
        _contains_keyword(
            title,
            term,
        )
        for term in TITLE_IMPORTANT_TERMS
    )

    if title_hits >= 3:

        score += 0.10

        reasons.append(
            "Strong title relevance"
        )

    elif title_hits == 2:

        score += 0.08

        reasons.append(
            "Good title relevance"
        )

    elif title_hits == 1:

        score += 0.05

        reasons.append(
            "Title contains relevant term"
        )

    # ======================================================
    # CONSULTANCY-SCOPE PROTECTION
    # ======================================================
    #
    # A tender can mention structural/building terminology while
    # actually being primarily a non-consultancy work package.
    #
    # If strong negative signals exist and there is no strong
    # consultancy service signal, apply an additional moderation.
    # ======================================================

    if (
        negative_found
        and not service_hits
    ):

        score *= 0.85

        reasons.append(
            "Scope caution: negative work-package "
            "signals without strong consultancy signal"
        )

    # ======================================================
    # SCORE NORMALIZATION
    # ======================================================

    score = max(
        0.0,
        min(
            score,
            1.0,
        ),
    )

    score = round(
        score,
        2,
    )

    reasons.append(
        f"Final Score = {score:.2f}"
    )

    return (
        score,
        reasons,
    )