import uuid
import unicodedata


def clean_text(value):
    """Fix garbled UTF-8 characters like â‚¹ → ₹ and â€" → —"""
    if not isinstance(value, str):
        return value if value is not None else ""

    try:
        fixed = value.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        fixed = value

    return unicodedata.normalize("NFKC", fixed)


def transform_opportunity(opportunity: dict) -> dict:

    score = float(opportunity.get("score", 0))

    if score >= 0.80:
        priority = "HIGH"
    elif score >= 0.55:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    why_selected = opportunity.get("why_selected", [])

    if isinstance(why_selected, list):
        why_selected = "; ".join(why_selected)

    intelligence = opportunity.get("intelligence", {})
    qualification = opportunity.get("qualification", {})

    organization = clean_text(opportunity.get("organization", ""))

    qualification_status = opportunity.get(
        "qualification_status",
        "REJECTED"
)

    extraction_confidence = 1.0

    if not organization:
        extraction_confidence -= 0.20

    if not opportunity.get("deadline"):
        extraction_confidence -= 0.10

    if not opportunity.get("location"):
        extraction_confidence -= 0.10

    extraction_confidence = round(max(extraction_confidence, 0), 2)

    return {

        "opportunity_id": str(uuid.uuid4()),

        "type": clean_text(
            opportunity.get("tender_type", "")
        ),

        "title": clean_text(
            opportunity.get("title", "")
        ),

        "organization": organization,

        "service_category": clean_text(
            opportunity.get("service_category")
            or intelligence.get(
                "service_category",
                ""
            )
        ),

        "location": clean_text(
            opportunity.get("location", "")
        ),

        "source": clean_text(
            opportunity.get("source", "")
        ),

        "source_url": opportunity.get(
            "source_url",
            ""
        ),

        "deadline": clean_text(
            opportunity.get("deadline", "")
        ),

        "summary": clean_text(
            opportunity.get("summary")
            or intelligence.get(
                "summary",
                ""
            )
        ),

        "contact_status": "NOT_CONTACTED",

        "opportunity_status": "NEW",

        "priority": priority,

        "score": round(score, 2),

        "reasoning": clean_text(
            opportunity.get(
                "reasoning",
                ""
            )
        ),

        "why_selected": why_selected,

        "assigned_to": "",

        # ----------------------------
        # Qualification Layer
        # ----------------------------
        "qualified": qualification_status == "QUALIFIED",

        "qualification_status": qualification_status,

        "qualification_score": opportunity.get(
            "qualification_score",
            score
        ),

        "recommended_action": opportunity.get(
            "recommended_action",
            ""
        ),

        "qualification": qualification,

        # ----------------------------
        # Intelligence Layer
        # ----------------------------
        "hermes_confidence": intelligence.get(
            "confidence",
            0
        ),

        "intelligence": intelligence,

        # ----------------------------
        # Dashboard Metadata
        # ----------------------------
        "core_matches": len(
            intelligence.get(
                "core_matches",
                []
            )
        ),

        "negative_matches": len(
            intelligence.get(
                "negative_matches",
                []
            )
        ),

        "extraction_confidence": extraction_confidence,

        "parser_version": "v2"
    }


def transform_opportunities(
    opportunities: list
) -> list:
    """
    Transform and preserve relevance order
    (input already sorted by scorer).
    """

    return [
        transform_opportunity(op)
        for op in opportunities
    ]


def to_sheet_format(op: dict) -> dict:
    return {
        "Opportunity_ID": op["opportunity_id"],
        "Type": op.get("type", ""),
        "Title": op.get("title", ""),
        "Organization": op.get("organization", ""),
        "Service_Category": op.get("service_category", ""),
        "Location": op.get("location", ""),
        "Source": op.get("source", ""),
        "Source_Link": op.get("source_url", ""),
        "Deadline": op.get("deadline", ""),
        "Contact_Status": op.get("contact_status", ""),
        "Opportunity_Status": op.get("opportunity_status", ""),
        "Priority": op.get("priority", ""),
        "Score": op.get("score", 0),
        "Qualified": op.get("qualified", False),
        "Qualification_Score": op.get("qualification_score", 0),
        "Recommended_Action": op.get("recommended_action", ""),
        "Qualification_Reasoning": op.get("reasoning", ""),
        "Summary": op.get("summary", ""),
        "Assigned_To": op.get("assigned_to", ""),
        "Last_Updated": "",
        "Date_Added": ""
    }