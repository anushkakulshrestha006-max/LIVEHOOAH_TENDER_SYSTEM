"""
Document Cleaner
================

This module provides a lightweight preprocessing layer between the
extractors (PDF/HTML) and the TenderParser.

Responsibilities
----------------
The DocumentCleaner is intentionally NOT aware of tenders.

It only performs conservative text cleanup:

    Raw Text
        ↓
    Normalized Unicode
        ↓
    Encoding Repair
        ↓
    Remove Error Pages
        ↓
    Remove Navigation
        ↓
    Remove Boilerplate
        ↓
    Remove Cookie Notices
        ↓
    Remove JavaScript Warnings
        ↓
    Normalize Whitespace
        ↓
    Remove Empty Lines
        ↓
    Remove Page Numbers
        ↓
    Remove Headers/Footers
        ↓
    Remove TOC
        ↓
    Remove Noisy Lines
        ↓
    Clean Text

The cleaner should NEVER perform tender parsing.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from collections import Counter
from typing import List
logger = logging.getLogger("livehooah")


class DocumentCleaner:
    """
    Conservative document preprocessing.

    This class intentionally avoids any tender-specific heuristics.
    """

    # ------------------------------------------------------------------ #
    # Error Pages
    # ------------------------------------------------------------------ #

    ERROR_PATTERNS = [

        re.compile(r"\b404\b", re.I),
        re.compile(r"\b403\b", re.I),
        re.compile(r"\b500\b", re.I),

        re.compile(r"page\s+not\s+found", re.I),
        re.compile(r"access\s+denied", re.I),
        re.compile(r"forbidden", re.I),
        re.compile(r"internal\s+server\s+error", re.I),
        re.compile(r"service\s+unavailable", re.I),
        re.compile(r"bad\s+gateway", re.I),
        re.compile(r"website\s+under\s+maintenance", re.I),
        re.compile(r"site\s+under\s+maintenance", re.I),

        re.compile(r"verify\s+you\s+are\s+human", re.I),
        re.compile(r"captcha", re.I),
        re.compile(r"cloudflare", re.I),

        re.compile(r"javascript\s+required", re.I),
        re.compile(r"please\s+enable\s+javascript", re.I),
        re.compile(r"cookies\s+required", re.I),
    ]

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #

    NAVIGATION_LINES = {

        "home",
        "about",
        "about us",
        "contact",
        "contact us",
        "login",
        "log in",
        "sign in",
        "register",
        "sign up",
        "search",
        "advanced search",
        "site map",
        "sitemap",
        "skip to content",
        "skip navigation",
        "accessibility",
        "help",
        "feedback",
        "quick links",
        "quick link",
        "navigation",
        "menu",
        "back",
        "next",
        "previous",
    }

    # ------------------------------------------------------------------ #
    # Boilerplate
    # ------------------------------------------------------------------ #

    BOILERPLATE_PATTERNS = [

        re.compile(r"privacy\s+policy", re.I),
        re.compile(r"terms\s+of\s+use", re.I),
        re.compile(r"terms\s+and\s+conditions", re.I),
        re.compile(r"all\s+rights\s+reserved", re.I),
        re.compile(r"copyright", re.I),
        re.compile(r"powered\s+by", re.I),
        re.compile(r"visitor\s+counter", re.I),
        re.compile(r"last\s+updated", re.I),
        re.compile(r"screen\s+reader", re.I),
        re.compile(r"accessibility\s+statement", re.I),
    ]

    # ------------------------------------------------------------------ #
    # Cookie Notices
    # ------------------------------------------------------------------ #

    COOKIE_PATTERNS = [

        re.compile(r"cookie\s+policy", re.I),
        re.compile(r"accept\s+cookies", re.I),
        re.compile(r"allow\s+cookies", re.I),
        re.compile(r"we\s+use\s+cookies", re.I),
        re.compile(r"manage\s+cookies", re.I),
    ]

    # ------------------------------------------------------------------ #
    # JavaScript Warnings
    # ------------------------------------------------------------------ #

    JS_PATTERNS = [

        re.compile(r"enable\s+javascript", re.I),
        re.compile(r"javascript\s+disabled", re.I),
        re.compile(r"javascript\s+required", re.I),
        re.compile(r"browser\s+not\s+supported", re.I),
        re.compile(r"please\s+wait", re.I),
        re.compile(r"loading\.\.\.", re.I),
    ]

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def clean(
        self,
        text: str,
    ) -> str:
        """
        Clean extracted text while preserving all meaningful content.
        """

        if not text:
            return ""

        logger.debug(
            "DocumentCleaner started (%d chars)",
            len(text),
        )

        text = self._normalize_unicode(text)
        text = self._fix_common_encoding_errors(text)
        text = self._normalize_line_endings(text)

        if self._is_error_page(text):

            logger.warning(
                "Rejected obvious error page."
            )

            return ""

        lines = text.split("\n")

        lines = self._normalize_whitespace(lines)
        lines = self._remove_empty_lines(lines)

        lines = self._remove_navigation_lines(lines)
        lines = self._remove_boilerplate(lines)
        lines = self._remove_cookie_notices(lines)
        lines = self._remove_javascript_warnings(lines)

        lines = self._remove_page_numbers(lines)
        lines = self._remove_repeated_headers_and_footers(lines)
        lines = self._remove_table_of_contents(lines)
        lines = self._remove_noisy_short_lines(lines)

        lines = self._remove_empty_lines(lines)

        cleaned = "\n".join(lines).strip()

        logger.debug(
            "DocumentCleaner complete (%d chars)",
            len(cleaned),
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Error Page Detection
    # ------------------------------------------------------------------ #

    def _is_error_page(
        self,
        text: str,
    ) -> bool:
        """
        Detect obvious error pages that should never
        reach the TenderParser.
        """

        sample = text[:5000]

        matches = 0

        for pattern in self.ERROR_PATTERNS:

            if pattern.search(sample):
                matches += 1

        return matches >= 2

    # ------------------------------------------------------------------ #
    # Unicode Normalization
    # ------------------------------------------------------------------ #

    def _normalize_unicode(
        self,
        text: str,
    ) -> str:

        return unicodedata.normalize(
            "NFKC",
            text,
        )

    def _fix_common_encoding_errors(
        self,
        text: str,
    ) -> str:

        replacements = {

            "â€“": "–",
            "â€”": "—",
            "â€˜": "'",
            "â€™": "'",
            "â€œ": '"',
            "â€": '"',
            "â€¢": "•",
            "â‚¹": "₹",
            "\uf0b7": "•",
            "\xa0": " ",
        }

        for bad, good in replacements.items():

            text = text.replace(
                bad,
                good,
            )

        return text

    def _normalize_line_endings(
        self,
        text: str,
    ) -> str:

        return (
            text.replace("\r\n", "\n")
                .replace("\r", "\n")
        )

    # ------------------------------------------------------------------ #
    # Whitespace
    # ------------------------------------------------------------------ #

    def _normalize_whitespace(
        self,
        lines: List[str],
    ) -> List[str]:

        cleaned = []

        for line in lines:

            line = re.sub(
                r"[ \t]+",
                " ",
                line,
            )

            cleaned.append(
                line.strip()
            )

        return cleaned

    def _remove_empty_lines(
        self,
        lines: List[str],
    ) -> List[str]:

        return [
            line
            for line in lines
            if line
        ]

    # ------------------------------------------------------------------ #
    # Navigation Removal
    # ------------------------------------------------------------------ #

    def _remove_navigation_lines(
        self,
        lines: List[str],
    ) -> List[str]:

        cleaned = []

        removed = 0

        for line in lines:

            if line.lower() in self.NAVIGATION_LINES:
                removed += 1
                continue

            cleaned.append(line)

        logger.debug(
            "Removed %d navigation lines.",
            removed,
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Boilerplate Removal
    # ------------------------------------------------------------------ #

    def _remove_boilerplate(
        self,
        lines: List[str],
    ) -> List[str]:

        cleaned = []

        removed = 0

        for line in lines:

            if any(
                p.search(line)
                for p in self.BOILERPLATE_PATTERNS
            ):
                removed += 1
                continue

            cleaned.append(line)

        logger.debug(
            "Removed %d boilerplate lines.",
            removed,
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Cookie Notices
    # ------------------------------------------------------------------ #

    def _remove_cookie_notices(
        self,
        lines: List[str],
    ) -> List[str]:

        cleaned = []

        for line in lines:

            if any(
                p.search(line)
                for p in self.COOKIE_PATTERNS
            ):
                continue

            cleaned.append(line)

        return cleaned

    # ------------------------------------------------------------------ #
    # JavaScript Warnings
    # ------------------------------------------------------------------ #

    def _remove_javascript_warnings(
        self,
        lines: List[str],
    ) -> List[str]:

        cleaned = []

        for line in lines:

            if any(
                p.search(line)
                for p in self.JS_PATTERNS
            ):
                continue

            cleaned.append(line)

        return cleaned
        # ------------------------------------------------------------------ #
    # Page Numbers
    # ------------------------------------------------------------------ #

    PAGE_NUMBER_PATTERNS = [

        re.compile(r"^page\s+\d+$", re.I),

        re.compile(
            r"^page\s+\d+\s+of\s+\d+$",
            re.I,
        ),

        re.compile(r"^\d+\s*/\s*\d+$"),

        re.compile(r"^\d+$"),

        re.compile(
            r"^-+\s*\d+\s*-+$"
        ),
    ]

    def _remove_page_numbers(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove standalone page numbers.

        Conservative:
            - Does not remove numbered clauses.
            - Does not remove table rows.
            - Only removes obvious pagination.
        """

        cleaned = []

        removed = 0

        for line in lines:

            if any(
                pattern.fullmatch(line)
                for pattern in self.PAGE_NUMBER_PATTERNS
            ):
                removed += 1
                continue

            cleaned.append(line)

        logger.debug(
            "Removed %d page numbers.",
            removed,
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Headers / Footers
    # ------------------------------------------------------------------ #

    def _remove_repeated_headers_and_footers(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove repeated running headers and footers.

        Rules

        ✓ repeated >= 3
        ✓ short
        ✓ not table rows
        ✓ not dates
        ✓ not monetary values
        ✓ not section titles
        """

        counter = Counter()

        for line in lines:

            if len(line) <= 120:
                counter[line] += 1

        repeated = set()

        for line, count in counter.items():

            if count < 3:
                continue

            lower = line.lower()

            # Preserve common tender headings.

            if lower in {

                "scope of work",
                "eligibility",
                "eligibility criteria",
                "important dates",
                "critical dates",
                "technical bid",
                "financial bid",
                "emd",
                "earnest money deposit",
                "tender fee",
                "document fee",
                "price bid",
                "commercial bid",
                "qualification",
                "general conditions",
                "special conditions",
                "evaluation criteria",
                "schedule",

            }:
                continue

            # Preserve table rows.

            if "|" in line:
                continue

            # Preserve monetary values.

            if re.search(
                r"(₹|rs\.?|inr)",
                lower,
            ):
                continue

            # Preserve dates.

            if re.search(
                r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
                line,
            ):
                continue

            repeated.add(line)

        cleaned = []

        removed = 0

        for line in lines:

            if line in repeated:
                removed += 1
                continue

            cleaned.append(line)

        logger.debug(
            "Removed %d repeated headers/footers.",
            removed,
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Table of Contents
    # ------------------------------------------------------------------ #

    TOC_PATTERNS = [

        re.compile(
            r"^table\s+of\s+contents$",
            re.I,
        ),

        re.compile(
            r"^contents$",
            re.I,
        ),

        re.compile(
            r"^index$",
            re.I,
        ),

        re.compile(
            r".+\.{3,}\s*\d+$"
        ),
    ]

    def _remove_table_of_contents(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove obvious TOC entries while preserving
        actual tender content.
        """

        cleaned = []

        removed = 0

        for line in lines:

            if any(
                pattern.fullmatch(line)
                for pattern in self.TOC_PATTERNS
            ):
                removed += 1
                continue

            cleaned.append(line)

        logger.debug(
            "Removed %d TOC entries.",
            removed,
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Noisy Short Lines
    # ------------------------------------------------------------------ #

    def _remove_noisy_short_lines(
        self,
        lines: List[str],
    ) -> List[str]:
        """
        Remove obvious navigation/menu fragments that
        survived extraction.

        This method is intentionally conservative.
        """

        cleaned = []

        removed = 0

        preserve = {

            "scope of work",
            "scope",

            "eligibility",
            "eligibility criteria",

            "emd",
            "earnest money",

            "tender fee",
            "document fee",

            "technical bid",
            "financial bid",

            "important dates",
            "critical dates",

            "qualification",

            "schedule",

            "annexure",
            "appendix",

            "description",
            "project description",

            "contact details",

        }

        for line in lines:

            lower = line.lower()

            # Never remove important section names.

            if lower in preserve:
                cleaned.append(line)
                continue

            # Never remove table rows.

            if "|" in line:
                cleaned.append(line)
                continue

            # Never remove numbered headings.

            if re.match(
                r"^\d+(\.\d+)*",
                line,
            ):
                cleaned.append(line)
                continue

            # Remove extremely short menu fragments.

            if (
                len(line) <= 3
                and line.isalpha()
            ):
                removed += 1
                continue

            # Remove symbol-only lines.

            if re.fullmatch(
                r"[-_=*.]{3,}",
                line,
            ):
                removed += 1
                continue

            cleaned.append(line)

        logger.debug(
            "Removed %d noisy lines.",
            removed,
        )

        return cleaned

    # ------------------------------------------------------------------ #
    # Diagnostics
    # ------------------------------------------------------------------ #

    def _log_statistics(
        self,
        original_lines: int,
        cleaned_lines: int,
    ) -> None:
        """
        Emit lightweight diagnostics for debugging.
        """

        logger.debug(
            (
                "DocumentCleaner | "
                "input_lines=%d | "
                "output_lines=%d | "
                "removed=%d"
            ),
            original_lines,
            cleaned_lines,
            original_lines - cleaned_lines,
        )

# ---------------------------------------------------------------------- #
# End of DocumentCleaner
# ---------------------------------------------------------------------- #