import hashlib
import re
from difflib import SequenceMatcher


class DeduplicationService:
    """
    Removes duplicate tenders discovered from multiple sources.

    Priority:
        1. URL
        2. Source URL
        3. Fingerprint
        4. Fuzzy title similarity
    """

    TITLE_SIMILARITY = 0.92

    def deduplicate(self, opportunities):

        if not opportunities:
            return []

        unique = []

        seen_urls = set()
        seen_fingerprints = set()

        for opportunity in opportunities:

            if self._is_duplicate(
                opportunity,
                unique,
                seen_urls,
                seen_fingerprints,
            ):
                continue

            unique.append(opportunity)

            url = (
                opportunity.get("url")
                or opportunity.get("source_url")
                or ""
            ).strip().lower()

            if url:
                seen_urls.add(url)

            seen_fingerprints.add(
                self._fingerprint(opportunity)
            )

        print(
            f"Deduplication: {len(opportunities)} -> {len(unique)}"
        )

        return unique

    # -----------------------------------------------------

    def _is_duplicate(
        self,
        opportunity,
        unique,
        seen_urls,
        seen_fingerprints,
    ):

        url = (
            opportunity.get("url")
            or opportunity.get("source_url")
            or ""
        ).strip().lower()

        if url and url in seen_urls:
            return True

        fingerprint = self._fingerprint(
            opportunity
        )

        if fingerprint in seen_fingerprints:
            return True

        title = self._normalize(
            opportunity.get("title", "")
        )

        organization = self._normalize(
            opportunity.get("organization", "")
        )

        deadline = self._normalize(
            opportunity.get("deadline", "")
        )

        for existing in unique:

            existing_title = self._normalize(
                existing.get("title", "")
            )

            similarity = SequenceMatcher(
                None,
                title,
                existing_title,
            ).ratio()

            if similarity < self.TITLE_SIMILARITY:
                continue

            existing_org = self._normalize(
                existing.get("organization", "")
            )

            existing_deadline = self._normalize(
                existing.get("deadline", "")
            )

            if (
                organization == existing_org
                and deadline == existing_deadline
            ):
                return True

        return False

    # -----------------------------------------------------

    def _fingerprint(
        self,
        opportunity,
    ):

        title = self._normalize(
            opportunity.get("title", "")
        )

        organization = self._normalize(
            opportunity.get("organization", "")
        )

        deadline = self._normalize(
            opportunity.get("deadline", "")
        )

        text = (
            title
            + "|"
            + organization
            + "|"
            + deadline
        )

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    # -----------------------------------------------------

    def _normalize(
        self,
        text,
    ):

        if not text:
            return ""

        text = text.lower()

        text = re.sub(
            r"[^\w\s]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()