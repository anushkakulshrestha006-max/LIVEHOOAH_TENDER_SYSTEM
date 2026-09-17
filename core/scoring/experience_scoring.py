"""
Legacy compatibility wrapper for LiveHooah opportunity ranking.

The authoritative scoring logic lives in:

    core.scoring.livehooah_matcher.compute_livehooah_score

This module intentionally does NOT implement a separate scoring system.

Its purpose is to preserve compatibility with older imports while ensuring
that all opportunities are ranked using the same LiveHooah matcher.
"""


def rank_opportunities(opportunities):
    """
    Rank opportunities using their existing LiveHooah score.

    The preferred pipeline flow is:

        compute_livehooah_score()
            ↓
        opportunity["score"]
            ↓
        rank_opportunities()

    If an opportunity does not already have a score, this function leaves it
    untouched rather than silently performing another scoring pass.

    This prevents duplicate scoring logic and keeps
    livehooah_matcher.compute_livehooah_score() as the single source of truth.

    Args:
        opportunities: list of opportunity dictionaries

    Returns:
        list: opportunities with valid positive scores, sorted descending.
    """

    if not opportunities:
        return []

    ranked = []

    for opportunity in opportunities:

        if not isinstance(opportunity, dict):
            continue

        score = opportunity.get("score")

        if score is None:
            continue

        try:
            score = float(score)
        except (TypeError, ValueError):
            continue

        # Reject blocked / irrelevant opportunities.
        if score <= 0:
            continue

        opportunity["score"] = round(score, 2)

        # Keep priority thresholds consistent with the LiveHooah
        # opportunity pipeline.
        if score >= 0.70:
            opportunity["priority"] = "HIGH"

        elif score >= 0.50:
            opportunity["priority"] = "MEDIUM"

        else:
            opportunity["priority"] = "LOW"

        # Preserve existing reasoning if available.
        if "why_selected" not in opportunity:
            opportunity["why_selected"] = []

        ranked.append(opportunity)

    ranked.sort(
        key=lambda opportunity: opportunity.get(
            "score",
            0
        ),
        reverse=True
    )

    return ranked