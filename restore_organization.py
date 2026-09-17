from pathlib import Path

p = Path("core/services/tender_parser.py")
text = p.read_text(encoding="utf-8")

marker = "    # ------------------------------------------------------------------\n    # Deadline Extraction"

if marker not in text:
    raise RuntimeError("Could not find Deadline Extraction marker.")

organization = '''    def _extract_organization(
        self,
        text: str,
        lines: List[str],
        title: str = "",
    ) -> str:
        """
        Extract the most likely issuing organization using:

        1. Explicit organization labels.
        2. Candidate generation from the document header.
        3. Candidate scoring.
        4. A full-document scan for known institutional name patterns.
        5. Hierarchical normalization.

        `title` is used purely for cross-validation: a candidate that
        is effectively a restatement of the tender title (i.e.
        scope-of-work language) is rejected even if it otherwise scored
        well, since a document's scope of work and its issuing
        organization cannot be the same text.
        """

        # --------------------------------------------------
        # Pass 1: Explicit labels
        # --------------------------------------------------

        for line_index, line in enumerate(lines[:150]):

            lower = line.lower()

            for label in self.ORGANIZATION_LABELS:

                label_pattern = (
                    rf"\\b{re.escape(label)}\\b"
                )

                label_match = re.search(
                    label_pattern,
                    lower,
                )

                if not label_match:
                    continue

                label_end = label_match.end()

                remainder = line[label_end:]

                has_field_separator = bool(
                    re.match(
                        r"\\s*[:\\-]\\s*",
                        remainder,
                    )
                )

                prose_prone_labels = {
                    "issued by",
                    "department",
                    "authority",
                    "owner",
                    "employer",
                    "client",
                }

                if (
                    label.lower() in prose_prone_labels
                    and not has_field_separator
                ):
                    continue

                parts = re.split(
                    rf"\\b{re.escape(label)}\\b"
                    r"\\s*[:\\-]\\s*",
                    line,
                    flags=re.IGNORECASE,
                    maxsplit=1,
                )

                if len(parts) <= 1:
                    continue

                candidate = (
                    self._clean_organization_candidate(
                        parts[1]
                    )
                )

                if candidate and self._is_invalid_organization_candidate(
                    candidate
                ):
                    continue

                if candidate:
                    candidate_score = self._score_organization_candidate(
                        candidate,
                        line_index,
                    )

                candidate_lower = candidate.lower()

                address_indicators = (
                    "ground floor",
                    "first floor",
                    "second floor",
                    "third floor",
                    "fourth floor",
                    "fifth floor",
                    "plot no",
                    "plot number",
                    "sector",
                    "sec.",
                    "road",
                    "street",
                    "lane",
                    "avenue",
                    "building",
                    "block",
                    "wing",
                    "estate",
                    "complex",
                    "premises",
                    "pincode",
                    "pin code",
                )

                has_address_noise = any(
                    indicator in candidate_lower
                    for indicator in address_indicators
                )

                has_contact_noise = bool(
                    re.search(
                        r"\\b(email|e-mail|phone|mobile|fax|telephone|tel)\\b",
                        candidate_lower,
                    )
                    or "@" in candidate
                    or re.search(
                        r"https?://|www\\.",
                        candidate_lower,
                    )
                )

                has_title_overlap = self._overlaps_with_title(
                    candidate,
                    title,
                )

                if (
                    candidate_score > 0
                    and not has_address_noise
                    and not has_contact_noise
                    and not has_title_overlap
                ):
                    return self._normalize_organization(candidate)

        # --------------------------------------------------
        # Pass 2: Dedicated institutional-name detection
        # --------------------------------------------------

        institution = self._extract_institution_name(
            lines,
            title,
        )

        if institution:
            return self._normalize_organization(institution)

        # --------------------------------------------------
        # Pass 3: Candidate generation and scoring
        # --------------------------------------------------

        candidates = self._generate_organization_candidates(
            lines
        )

        scored = []

        for candidate, idx in candidates:

            candidate = (
                self._clean_organization_candidate(
                    candidate
                )
            )

            if not candidate:
                continue

            if self._is_invalid_organization_candidate(candidate):
                continue

            if self._overlaps_with_title(candidate, title):
                continue

            score = self._score_organization_candidate(
                candidate,
                idx,
            )

            if score <= 0:
                continue

            scored.append(
                (
                    score,
                    candidate,
                )
            )

        if scored:

            scored.sort(
                key=lambda item: item[0],
                reverse=True,
            )

            return self._normalize_organization(
                scored[0][1]
            )

        # --------------------------------------------------
        # Pass 4: Full-document institutional-name scan
        # --------------------------------------------------

        institution = self._extract_institution_name(
            lines,
            title,
        )

        if institution:
            return self._normalize_organization(institution)

        return ""

    # ------------------------------------------------------------------
'''

text = text.replace(
    marker,
    organization + "    # Deadline Extraction",
    1,
)

p.write_text(text, encoding="utf-8")

print("RESTORED: _extract_organization")
print("FILE:", p)
