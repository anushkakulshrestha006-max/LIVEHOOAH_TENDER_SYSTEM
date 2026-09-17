from typing import Dict


class GPTQualifier:

    QUALIFIED_CATEGORIES = {
        "structural consultancy",
        "structural audit",
        "proof checking",
        "retrofit consultancy",
    }

    REVIEW_CATEGORIES = {
        "industrial building",
        "warehouse",
        "peb design",
    }

    def qualify(
        self,
        opportunity: Dict
    ) -> Dict:

        intelligence = opportunity.get(
            "intelligence",
            {}
        )

        confidence = float(
            intelligence.get(
                "confidence",
                0
            )
        )

        service_category = (
            intelligence.get(
                "service_category",
                ""
            )
            .strip()
            .lower()
        )

        livehooah_score = float(
            opportunity.get(
                "score",
                0
            )
        )

        # ----------------------------------
        # HIGH-CONFIDENCE CONSULTANCY WORK
        # ----------------------------------

        if (
            service_category
            in self.QUALIFIED_CATEGORIES
            and confidence >= 0.60
        ):

            qualified = True
            action = "PURSUE"

            reasoning = (
                f"Qualified consultancy opportunity "
                f"({service_category}). "
                f"Confidence={confidence}"
            )

        # ----------------------------------
        # POSSIBLE OPPORTUNITY
        # ----------------------------------

        elif (
            service_category
            in self.REVIEW_CATEGORIES
            and livehooah_score >= 0.50
        ):

            qualified = True
            action = "REVIEW"

            reasoning = (
                f"Relevant sector opportunity "
                f"({service_category}) "
                f"but consultancy scope should be verified. "
                f"Score={livehooah_score}"
            )

        # ----------------------------------
        # LOW RELEVANCE
        # ----------------------------------

        else:

            qualified = False
            action = "REJECT"

            reasoning = (
                f"Insufficient structural consultancy "
                f"signals. "
                f"Category={service_category}, "
                f"Confidence={confidence}, "
                f"Score={livehooah_score}"
            )

        qualification_score = round(
            (
                confidence * 0.60
                + livehooah_score * 0.40
            ),
            2
        )

        return {
            "qualified": qualified,

            "qualification_score":
                qualification_score,

            "recommended_action":
                action,

            "project_type":
                service_category,

            "reasoning":
                reasoning
        }