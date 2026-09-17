from config.livehooah_experience import LIVEHOOAH_EXPERIENCE, TIER_WEIGHTS
from config.livehooah_keywords import LIVEHOOAH_KEYWORDS


# -----------------------------
# 1. EXPERIENCE MATCH + EXPLANATION
# -----------------------------
def experience_match_score(tender: dict):
    location = tender.get("location", "").lower()
    title = tender.get("title", "").lower()

    score = 0.0
    reasons = []

    for region, data in LIVEHOOAH_EXPERIENCE.items():

        # LOCATION MATCH
        if any(loc.lower() in location for loc in data["locations"]):
            score += 0.35
            reasons.append(f"Matches {region} experience region")

        # PROJECT TYPE MATCH
        matched_types = [
            pt for pt in data["project_types"]
            if pt.lower() in title
        ]

        if matched_types:
            score += 0.35
            reasons.append(
                f"Matches project type: {', '.join(matched_types)}"
            )

        # CLIENT SIGNAL
        matched_clients = [
            c for c in data["clients"]
            if c.lower() in title
        ]

        if matched_clients:
            score += 0.1
            reasons.append(
                f"Related to known client ecosystem: {', '.join(matched_clients)}"
            )

    return min(score, 1.0), reasons


# -----------------------------
# 2. DOMAIN SCORING + EXPLANATION
# -----------------------------
def domain_score(tender: dict):
    text = f"{tender.get('title','')} {tender.get('source','')}".lower()

    score = 0.0
    reasons = []

    for kw in LIVEHOOAH_KEYWORDS["high_priority"]:
        if kw in text:
            score += 0.15
            reasons.append(f"High-priority keyword match: {kw}")

    for kw in LIVEHOOAH_KEYWORDS["engineering"]:
        if kw in text:
            score += 0.08
            reasons.append(f"Engineering keyword match: {kw}")

    for kw in LIVEHOOAH_KEYWORDS["infrastructure"]:
        if kw in text:
            score += 0.10
            reasons.append(f"Infrastructure keyword match: {kw}")

    return min(score, 1.0), reasons


# -----------------------------
# 3. PENALTY SYSTEM + EXPLANATION
# -----------------------------
def penalty_score(tender: dict):
    text = f"{tender.get('title','')} {tender.get('source','')}".lower()

    penalty = 0.0
    reasons = []

    if "maintenance" in text:
        penalty += 0.25
        reasons.append("Maintenance-heavy project (lower strategic fit)")

    if "repair" in text:
        penalty += 0.15
        reasons.append("Repair work (low capex relevance)")

    if "airport" in text:
        penalty += 0.4
        reasons.append("Airport infrastructure (outside core focus)")

    if "rail" in text or "metro" in text:
        penalty += 0.35
        reasons.append("Rail/metro infrastructure (non-core domain)")

    return min(penalty, 1.0), reasons


# -----------------------------
# 4. FINAL SCORE + WHY_SELECTED
# -----------------------------
def calculate_relevance_score(tender: dict):

    exp_score, exp_reason = experience_match_score(tender)
    dom_score, dom_reason = domain_score(tender)
    pen_score, pen_reason = penalty_score(tender)

    final_score = (
        (exp_score * 0.45) +
        (dom_score * 0.45) -
        (pen_score * 0.40)
    )

    final_score = round(max(min(final_score, 1.0), 0.0), 2)

    why_selected = exp_reason + dom_reason

    # Only keep strong reasons (clean output)
    why_selected = why_selected[:5]

    return final_score, why_selected


# -----------------------------
# 5. RANKING FUNCTION
# -----------------------------
def rank_opportunities(opportunities: list):

    for opp in opportunities:
        score, reasons = calculate_relevance_score(opp)
        opp["relevance_score"] = score
        opp["why_selected"] = reasons

    return sorted(
        opportunities,
        key=lambda x: x["relevance_score"],
        reverse=True
    )