"""
Focused behavioral test suite for core.scoring.livehooah_matcher.

This test suite establishes the baseline behavioral contract of the CURRENT
implementation of livehooah_matcher.py.

IMPORTANT:
- Establishes current behavior before any code modifications.
- Contains a regression test for the verified defect in metadata_score()
  where explicit None values are converted to string "None" and incorrectly
  counted as populated.
- Documents parser field naming differences (email/phone vs contact_email/contact_phone).
"""

from datetime import date, datetime, timedelta
import pytest

from core.scoring.livehooah_matcher import (
    compute_livehooah_score,
    parse_deadline,
    freshness_score,
    metadata_score,
    apply_region_score,
    _contains_keyword,
    LIVEHOOAH_CORE,
    SECONDARY_MATCHES,
    REAL_OPPORTUNITY_TERMS,
    LIVEHOOAH_OPPORTUNITY_TERMS,
    REGION_BOOST,
    NON_PREFERRED_REGION_PENALTY,
    NEGATIVE_KEYWORDS,
    PREFERRED_ORGANIZATIONS,
    OFFICIAL_SOURCES,
    TITLE_IMPORTANT_TERMS,
)


# ==============================================================================
# 1. STRONG STRUCTURAL CONSULTANCY OPPORTUNITY
# ==============================================================================

def test_strong_structural_consultancy_positive_score():
    """
    A core structural engineering consultancy opportunity with valid metadata,
    official source, and future deadline receives a high positive score (>= 0.60).
    """
    future_deadline = (date.today() + timedelta(days=45)).isoformat()
    opportunity = {
        "title": "Empanelment of Structural Consultants for Building Projects",
        "description": "Structural engineering consultancy, structural design, and proof checking for high-rise towers",
        "organization": "CPWD",
        "deadline": future_deadline,
        "location": "New Delhi",
        "source": "etenders.gov.in",
        "source_url": "https://etenders.gov.in/eprocure/app",
        "contact_email": "consultant@cpwd.gov.in",
        "contact_phone": "011-23000000",
    }

    score, reasons = compute_livehooah_score(opportunity)

    assert score >= 0.60
    assert any("core capability matches" in r for r in reasons)
    assert any("Tender opportunity detected" in r for r in reasons)
    assert any("Relevant consultancy service" in r for r in reasons)
    assert any("Preferred region" in r for r in reasons)
    assert any("Preferred organization" in r for r in reasons)
    assert any("Official source" in r for r in reasons)


# ==============================================================================
# 2. BLOCKED INFRASTRUCTURE KEYWORD HARD REJECTION
# ==============================================================================

def test_blocked_infrastructure_keyword_hard_rejected():
    """
    An opportunity containing any keyword from LIVEHOOAH_KEYWORDS['blocked']
    must be immediately hard rejected with score 0.0 and a blocked reason,
    even if it also contains structural keywords.
    """
    opportunity = {
        "title": "Structural design consultancy for National Highway and Bridge construction",
        "description": "Structural analysis and proof checking for highway bridge",
        "organization": "NHAI",
        "location": "Delhi",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
    }

    score, reasons = compute_livehooah_score(opportunity)

    assert score == 0.0
    assert len(reasons) == 1
    assert "Blocked keyword:" in reasons[0]


# ==============================================================================
# 3. NO STRUCTURAL RELEVANCE HARD REJECTION
# ==============================================================================

def test_no_structural_relevance_hard_rejected():
    """
    An opportunity with no core structural keywords and no secondary fallback
    keywords must be immediately rejected with score 0.0.
    """
    opportunity = {
        "title": "Procurement of office laptops and printing stationery",
        "description": "Supply and maintenance of IT hardware",
        "organization": "CPWD",
        "location": "Delhi",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }

    score, reasons = compute_livehooah_score(opportunity)

    assert score == 0.0
    assert reasons == ["No structural relevance detected"]


# ==============================================================================
# 4. SECONDARY STRUCTURAL FALLBACK
# ==============================================================================

def test_secondary_structural_fallback():
    """
    When an opportunity contains no LIVEHOOAH_CORE terms, but contains terms from
    SECONDARY_MATCHES (e.g. 'commercial', 'building', 'tower'), it should receive
    a non-zero score with a 'Weak structural relevance (secondary fallback)' reason.
    """
    opportunity = {
        "title": "Tender for commercial building tower facilities",
        "description": "General management of commercial building facilities",
        "organization": "Municipal Corporation",
        "location": "Delhi",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }

    score, reasons = compute_livehooah_score(opportunity)

    assert score > 0.0
    assert any("secondary fallback" in r.lower() for r in reasons)


# ==============================================================================
# 5. PROCUREMENT SIGNAL AFFECTS SCORE
# ==============================================================================

def test_procurement_signal_affects_score():
    """
    Presence of procurement language (e.g. 'tender', 'rfp') adds a +0.20 bonus,
    whereas absence of procurement language applies a 0.80 penalty factor.
    """
    base_opp = {
        "title": "Structural engineering consultancy for residential tower",
        "description": "Detailed structural analysis and design drawings",
        "location": "Delhi",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
    }

    with_procurement = dict(base_opp)
    with_procurement["title"] = "Notice Inviting Tender for structural engineering consultancy"

    score_with, reasons_with = compute_livehooah_score(with_procurement)
    score_without, reasons_without = compute_livehooah_score(base_opp)

    assert any("Tender opportunity detected" in r for r in reasons_with)
    assert any("Weak tender signal" in r for r in reasons_without)
    assert score_with > score_without


# ==============================================================================
# 6. CONSULTANCY SERVICE SIGNAL AFFECTS SCORE
# ==============================================================================

def test_consultancy_service_signal_affects_score():
    """
    Presence of explicit LiveHooah consultancy terms adds up to +0.20 bonus,
    whereas absence applies a 0.90 penalty factor.
    """
    base_opp = {
        "title": "Tender for warehouse building construction",
        "description": "Warehouse and logistics facility",
        "location": "Delhi",
        "deadline": (date.today() + timedelta(days=30)).isoformat(),
    }

    with_service = dict(base_opp)
    with_service["description"] = (
        "Warehouse and logistics facility structural consultant for "
        "proof checking, structural audit, and peer review"
    )

    score_with, reasons_with = compute_livehooah_score(with_service)
    score_without, reasons_without = compute_livehooah_score(base_opp)

    assert any("Relevant consultancy service" in r for r in reasons_with)
    assert any("Weak consultancy relevance" in r for r in reasons_without)
    assert score_with > score_without


# ==============================================================================
# 7. PREFERRED REGION BOOST
# ==============================================================================

def test_preferred_region_boost():
    """
    Locations matching REGION_BOOST (e.g. Delhi, Gurgaon, Noida) receive a
    positive region score (+0.05 to +0.10).
    """
    reasons = []
    boost_delhi = apply_region_score("Project located in Delhi NCR", reasons)
    assert boost_delhi == 0.10
    assert any("Preferred region (delhi)" in r for r in reasons)

    reasons_gurgaon = []
    boost_gurgaon = apply_region_score("Project site in Gurgaon", reasons_gurgaon)
    assert boost_gurgaon == 0.10
    assert any("Preferred region (gurgaon)" in r for r in reasons_gurgaon)


# ==============================================================================
# 8. NON-PREFERRED REGION PENALTY (INCLUDING CURRENT PUNJAB BEHAVIOR)
# ==============================================================================

def test_non_preferred_region_penalty():
    """
    Locations in NON_PREFERRED_REGION_PENALTY receive a negative penalty.
    Documents the CURRENT behavior for Kerala (-0.06) and Punjab (-0.03).
    """
    reasons_kerala = []
    penalty_kerala = apply_region_score("Project in Kerala", reasons_kerala)
    assert penalty_kerala == -0.06
    assert any("Non-preferred region (kerala) (-0.06)" in r for r in reasons_kerala)

    # Current behavior: Punjab is penalized (-0.03) in the current implementation
    reasons_punjab = []
    penalty_punjab = apply_region_score("Project in Ludhiana, Punjab", reasons_punjab)
    assert penalty_punjab == -0.03
    assert any("Non-preferred region (punjab) (-0.03)" in r for r in reasons_punjab)


# ==============================================================================
# 9. PREFERRED ORGANIZATION SCORING
# ==============================================================================

def test_preferred_organization_score():
    """
    Tenders from organizations in PREFERRED_ORGANIZATIONS (e.g. CPWD, NBCC, IIT)
    receive an organization quality bonus.
    """
    opp_cpwd = {
        "title": "Tender for structural consultancy services",
        "organization": "Central Public Works Department (CPWD)",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }
    opp_generic = {
        "title": "Tender for structural consultancy services",
        "organization": "Private Commercial Entity",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }

    score_cpwd, reasons_cpwd = compute_livehooah_score(opp_cpwd)
    score_generic, reasons_generic = compute_livehooah_score(opp_generic)

    assert any("Preferred organization (cpwd)" in r for r in reasons_cpwd)
    assert not any("Preferred organization" in r for r in reasons_generic)
    assert score_cpwd > score_generic


# ==============================================================================
# 10. OFFICIAL SOURCE SCORING
# ==============================================================================

def test_official_source_score():
    """
    Tenders originating from official portals (e.g. etenders.gov.in, gem.gov.in)
    receive an official source bonus.
    """
    opp_official = {
        "title": "Tender for structural consultancy services",
        "source": "etenders.gov.in",
        "source_url": "https://etenders.gov.in/eprocure/app",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }
    opp_other = {
        "title": "Tender for structural consultancy services",
        "source": "random-blog.com",
        "source_url": "https://random-blog.com/post/123",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }

    score_off, reasons_off = compute_livehooah_score(opp_official)
    score_oth, reasons_oth = compute_livehooah_score(opp_other)

    assert any("Official source (etenders.gov.in)" in r for r in reasons_off)
    assert not any("Official source" in r for r in reasons_oth)
    assert score_off > score_oth


# ==============================================================================
# 11. FRESHNESS SCORING BEHAVIOR
# ==============================================================================

def test_freshness_scoring():
    """
    Freshness scoring behaves according to the days remaining until deadline:
    - > 30 days: +0.15 (Fresh opportunity)
    - 8 to 30 days: +0.12 (Active tender)
    - 1 to 7 days: +0.08 (Closing within 7 days)
    - Expired (< 0 days): +0.00 (Expired tender)
    - Missing deadline: +0.02 (Deadline missing)
    """
    today = date.today()

    score_fresh, reason_fresh = freshness_score((today + timedelta(days=40)).isoformat())
    assert score_fresh == 0.15
    assert reason_fresh == "Fresh opportunity"

    score_active, reason_active = freshness_score((today + timedelta(days=20)).isoformat())
    assert score_active == 0.12
    assert reason_active == "Active tender"

    score_closing, reason_closing = freshness_score((today + timedelta(days=5)).isoformat())
    assert score_closing == 0.08
    assert reason_closing == "Closing within 7 days"

    score_expired, reason_expired = freshness_score((today - timedelta(days=5)).isoformat())
    assert score_expired == 0.00
    assert reason_expired == "Expired tender"

    score_missing, reason_missing = freshness_score(None)
    assert score_missing == 0.02
    assert reason_missing == "Deadline missing"


# ==============================================================================
# 12. METADATA COMPLETENESS BEHAVIOR
# ==============================================================================

def test_metadata_completeness_behavior():
    """
    Populated string fields are credited at 0.015 per field, capped at 0.12 (8 fields).
    """
    full_opp = {
        "title": "Title",
        "organization": "Org",
        "deadline": "2026-12-31",
        "location": "Location",
        "description": "Description",
        "contact_email": "email@test.com",
        "contact_phone": "1234567890",
        "source": "gem.gov.in",
    }
    score_full, reason_full = metadata_score(full_opp)
    assert score_full == 0.12
    assert "8/8 metadata fields populated" in reason_full

    partial_opp = {
        "title": "Title",
        "organization": "Org",
    }
    score_partial, reason_partial = metadata_score(partial_opp)
    assert score_partial == pytest.approx(2 * 0.015)
    assert "2/8 metadata fields populated" in reason_partial


# ==============================================================================
# 13. NEGATIVE KEYWORD PENALTIES
# ==============================================================================

def test_negative_keyword_penalties():
    """
    Presence of non-core negative terms (e.g. 'housekeeping', 'manpower supply', 'roads')
    deducts penalty from the score and documents the reason.
    """
    opp_clean = {
        "title": "Tender for structural consultancy for industrial building",
        "description": "Structural analysis and engineering consultancy",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }
    opp_negative = dict(opp_clean)
    opp_negative["description"] = (
        "Structural analysis and engineering consultancy along with "
        "housekeeping and manpower supply"
    )

    score_clean, reasons_clean = compute_livehooah_score(opp_clean)
    score_negative, reasons_negative = compute_livehooah_score(opp_negative)

    assert any("Negative keywords:" in r for r in reasons_negative)
    assert score_clean > score_negative


# ==============================================================================
# 14. TITLE RELEVANCE BONUS
# ==============================================================================

def test_title_relevance_bonus():
    """
    Titles containing terms from TITLE_IMPORTANT_TERMS receive additive bonuses:
    - 1 hit: +0.05
    - 2 hits: +0.08
    - >= 3 hits: +0.10
    """
    opp_3_hits = {
        "title": "RFP for structural consultancy and retrofit",
        "description": "Consultancy services for building",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }
    opp_1_hit = {
        "title": "Tender for building structural work",
        "description": "Consultancy services for building",
        "deadline": (date.today() + timedelta(days=20)).isoformat(),
    }

    score_3, reasons_3 = compute_livehooah_score(opp_3_hits)
    score_1, reasons_1 = compute_livehooah_score(opp_1_hit)

    assert any("Strong title relevance" in r for r in reasons_3)
    assert any("Title contains relevant term" in r for r in reasons_1)
    assert score_3 > score_1


# ==============================================================================
# 15. FINAL SCORE REMAINS WITHIN 0.0 - 1.0 BOUNDS
# ==============================================================================

def test_final_score_bounds():
    """
    The final score must strictly remain within [0.0, 1.0] under all conditions.
    """
    # Highly matched opportunity
    max_opp = {
        "title": "RFP for structural consultancy and proof checking for high-rise tower",
        "description": "Structural engineering consultancy, design, audit, peer review, retrofitting for warehouse and logistics park",
        "organization": "CPWD",
        "deadline": (date.today() + timedelta(days=60)).isoformat(),
        "location": "Delhi NCR",
        "source": "etenders.gov.in",
        "source_url": "https://etenders.gov.in/eprocure/app",
        "contact_email": "cpwd@gov.in",
        "contact_phone": "011-23000000",
    }
    score_max, _ = compute_livehooah_score(max_opp)
    assert 0.0 <= score_max <= 1.0

    # Opportunity with multiple penalties
    penalized_opp = {
        "title": "Structural repair with housekeeping, sanitation, security, and vehicle hiring",
        "description": "Building structural facility with housekeeping, catering services, transportation services",
        "location": "Kerala",
        "deadline": (date.today() - timedelta(days=10)).isoformat(),
    }
    score_pen, _ = compute_livehooah_score(penalized_opp)
    assert 0.0 <= score_pen <= 1.0


# ==============================================================================
# 16. EXPLICIT NONE VALUES IN METADATA (REGRESSION DEFECT TEST)
# ==============================================================================

def test_metadata_score_explicit_none_should_not_count_as_populated():
    """
    REGRESSION TEST FOR VERIFIED DEFECT.

    Specification / Expected Correct Behavior:
    When metadata fields in an opportunity have explicit None values
    (which is the standard output of TenderParser for missing fields),
    those fields must NOT be counted as populated.

    Current Implementation Behavior (Known Defect):
    metadata_score() evaluates:
        bool(str(opportunity.get(field, "")).strip())
    When opportunity[field] is None, str(None) becomes "None", which is truthy.
    Consequently, missing fields with None are falsely counted as populated,
    awarding full metadata completeness credit to an essentially blank document.

    This test asserts the EXPECTED CORRECT behavior:
    An opportunity with only 'title' populated and all other fields None
    should report 1/8 populated fields, NOT 8/8.

    Under the current implementation, this test is expected to FAIL.
    """
    opp = {
        "title": "Empanelment of Structural Consultants",
        "organization": None,
        "deadline": None,
        "location": None,
        "description": None,
        "contact_email": None,
        "contact_phone": None,
        "source": None,
    }

    score, reason = metadata_score(opp)

    # Expected specification: only 1 field (title) is populated
    assert "1/8 metadata fields populated" in reason
    assert score == pytest.approx(1 * 0.015)


# ==============================================================================
# 17. PARSER FIELD NAMING DOCUMENTATION TEST (EMAIL/PHONE VS CONTACT_EMAIL/PHONE)
# ==============================================================================

def test_metadata_parser_field_names_email_phone():
    """
    Documents current field naming behavior:
    metadata_score() currently inspects 'contact_email' and 'contact_phone'.
    TenderParser outputs 'email' and 'phone'.

    This test verifies that under the current implementation, 'email' and 'phone'
    are NOT counted by metadata_score() unless mapped to 'contact_email' and 'contact_phone'.
    """
    # Raw TenderParser output style (uses 'email' and 'phone')
    parser_output_opp = {
        "title": "Structural consultancy",
        "organization": "CPWD",
        "email": "engineer@cpwd.gov.in",
        "phone": "011-12345678",
    }
    score_raw, reason_raw = metadata_score(parser_output_opp)
    # Under current code, 'email' and 'phone' are ignored; only title and organization count (2/8)
    assert "2/8 metadata fields populated" in reason_raw

    # When mapped to 'contact_email' and 'contact_phone'
    pipeline_mapped_opp = {
        "title": "Structural consultancy",
        "organization": "CPWD",
        "contact_email": "engineer@cpwd.gov.in",
        "contact_phone": "011-12345678",
    }
    score_mapped, reason_mapped = metadata_score(pipeline_mapped_opp)
    # Under current code, contact_email and contact_phone are recognized (4/8)
    assert "4/8 metadata fields populated" in reason_mapped


# ==============================================================================
# 18. NONE VALUES DO NOT CREATE FALSE STRUCTURAL RELEVANCE OR INFLATE SCORE
# ==============================================================================

def test_none_values_do_not_create_false_structural_match_or_inflate_score():
    """
    Verifies that explicit None values across opportunity fields:
    1. Do not cause the stringified word 'None' / 'none' to match any structural
       keyword in LIVEHOOAH_CORE or SECONDARY_MATCHES.
    2. Ensure that an opportunity consisting solely of None fields is rejected
       with score 0.0 ('No structural relevance detected').
    3. Ensure that a non-structural opportunity with None fields does not gain
       relevance or score inflation compared to empty string fields.
    4. Confirm that an opportunity with explicit None fields yields identical
       relevance scoring to one with empty string or omitted fields.
    """
    # Case A: Entirely None fields - must be rejected with 0.0
    all_none_opp = {
        "title": None,
        "description": None,
        "summary": None,
        "location": None,
        "organization": None,
        "source": None,
        "source_url": None,
        "deadline": None,
    }
    score_all_none, reasons_all_none = compute_livehooah_score(all_none_opp)
    assert score_all_none == 0.0
    assert reasons_all_none == ["No structural relevance detected"]

    # Case B: Non-structural tender with explicit None fields vs empty string fields
    non_structural_none = {
        "title": "Supply of office stationery and computers",
        "description": None,
        "summary": None,
        "location": None,
        "organization": None,
        "source": None,
        "source_url": None,
        "deadline": None,
    }
    non_structural_empty = {
        "title": "Supply of office stationery and computers",
        "description": "",
        "summary": "",
        "location": "",
        "organization": "",
        "source": "",
        "source_url": "",
        "deadline": "",
    }
    score_ns_none, reasons_ns_none = compute_livehooah_score(non_structural_none)
    score_ns_empty, reasons_ns_empty = compute_livehooah_score(non_structural_empty)
    assert score_ns_none == 0.0
    assert score_ns_empty == 0.0
    assert reasons_ns_none == reasons_ns_empty == ["No structural relevance detected"]

    # Case C: Valid structural tender with None vs empty fields produces identical score & reasons
    structural_none = {
        "title": "Empanelment of Structural Consultants for Building Projects",
        "description": None,
        "summary": None,
        "location": None,
        "organization": None,
        "source": None,
        "source_url": None,
        "deadline": None,
    }
    structural_empty = {
        "title": "Empanelment of Structural Consultants for Building Projects",
        "description": "",
        "summary": "",
        "location": "",
        "organization": "",
        "source": "",
        "source_url": "",
        "deadline": "",
    }
    score_st_none, reasons_st_none = compute_livehooah_score(structural_none)
    score_st_empty, reasons_st_empty = compute_livehooah_score(structural_empty)
    assert score_st_none == score_st_empty
    assert reasons_st_none == reasons_st_empty
