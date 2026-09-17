import logging
from typing import List, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("livehooah")


class SourceResolver:
    """
    Resolves a search result URL into the best available source.

    Priority
    --------
        Relevant PDF
            ↓
        Official Government Tender Page
            ↓
        Procurement Portal
            ↓
        Original URL

    Responsibilities
    ----------------
    • Follow redirects
    • Inspect HTML pages
    • Discover relevant document links

    NOT responsible for:
    • Downloading documents
    • Parsing tenders
    • Metadata extraction

    Important:
    This resolver must not blindly select any PDF found on a page.
    Many government websites contain unrelated PDFs such as acts,
    policies, reports, brochures, and historical documents.
    """

    GOV_DOMAINS = (
        ".gov.in",
        ".nic.in",
        "eprocure.gov.in",
        "etenders.gov.in",
        "gem.gov.in",
        "ireps.gov.in",
        "coalindiatenders.nic.in",
    )

    AGGREGATOR_DOMAINS = (
        "bidassist",
        "tenderdetail",
        "tendersinfo",
        "tender247",
        "tendernews",
        "tenderbazaar",
    )

    PDF_KEYWORDS = (
        ".pdf",
        "download",
        "document",
        "nit",
        "tendernotice",
        "tender_notice",
        "notice",
        "rfp",
        "eoi",
        "bid",
        "empanelment",
        "corrigendum",
    )

    TENDER_KEYWORDS = (
        "tender",
        "rfp",
        "eoi",
        "bid",
        "corrigendum",
        "notice",
        "empanelment",
        "expression of interest",
        "request for proposal",
        "consultant",
        "consultancy",
        "structural",
        "architectural",
        "engineering",
        "proof checking",
        "structural audit",
    )

    IRRELEVANT_DOCUMENT_KEYWORDS = (
        "act",
        "rules",
        "policy",
        "policies",
        "annual report",
        "brochure",
        "handbook",
        "manual",
        "guidelines",
        "notification",
        "circular",
        "budget",
        "order",
        "government order",
        "privacy",
        "terms",
        "publication",
        "magazine",
        "newsletter",
        "calendar",
        "recruitment",
        "admission",
        "prospectus",
    )

    INVALID_PREFIXES = (
        "javascript:",
        "mailto:",
        "tel:",
        "#",
    )

    def __init__(self, timeout: int = 20):
        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/138.0 Safari/537.36"
                )
            }
        )

    # ------------------------------------------------------------------

    def resolve(self, url: str) -> str:
        """
        Resolve a search result into the most useful source.

        The original URL is preserved unless a clearly better,
        relevant source is discovered.

        This is intentionally conservative. Selecting an unrelated
        PDF is worse than returning the original HTML tender page.
        """

        if not url:
            return url

        url = self._normalize(url)

        if self._is_pdf(url):
            return url

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                allow_redirects=True,
            )

            response.raise_for_status()

            final_url = self._normalize(response.url)

            if self._is_pdf(final_url):
                return final_url

            if not self._is_html(response):
                return final_url

            try:
                soup = BeautifulSoup(
                    response.text,
                    "lxml",
                )
            except Exception:
                soup = BeautifulSoup(
                    response.text,
                    "html.parser",
                )

            candidates = self._extract_links(
                soup=soup,
                base_url=final_url,
            )

            best = self._choose_best(
                candidates=candidates,
                page_url=final_url,
            )

            if best:
                logger.debug(
                    "Source resolved to relevant document | "
                    "original=%s | resolved=%s",
                    url,
                    best,
                )

                return best

            logger.debug(
                "No clearly relevant document found | "
                "returning original page | url=%s",
                final_url,
            )

            return final_url

        except requests.RequestException as e:
            logger.debug(
                "Source resolution failed for %s (%s)",
                url,
                e,
            )

            return url

    # ------------------------------------------------------------------

    def _extract_links(
        self,
        soup: BeautifulSoup,
        base_url: str,
    ) -> List[Tuple[str, str]]:

        links = []

        for tag in soup.find_all("a", href=True):
            href = str(tag.get("href") or "").strip()

            if not href:
                continue

            lower = href.lower()

            if lower.startswith(self.INVALID_PREFIXES):
                continue

            absolute = urljoin(base_url, href)

            absolute = self._normalize(absolute)

            link_text = tag.get_text(" ", strip=True)

            links.append((absolute, link_text))

        unique = {}

        for link, text in links:
            if link not in unique:
                unique[link] = text

        return [(link, text) for link, text in unique.items()]

    # ------------------------------------------------------------------

    def _choose_best(
        self,
        candidates: List[Tuple[str, str]],
        page_url: str,
    ) -> str:

        if not candidates:
            return ""

        scored = []

        page_context = self._build_page_context(page_url)

        for link, link_text in candidates:
            score = self._score_candidate(
                link=link,
                link_text=link_text,
                page_context=page_context,
            )

            if score is None:
                continue

            scored.append((score, link, link_text))

        if not scored:
            return ""

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_link, best_text = scored[0]

        if best_score < 30:
            logger.debug(
                "No candidate passed source resolution threshold | "
                "best_score=%s | link=%s | text=%s",
                best_score,
                best_link,
                best_text,
            )

            return ""

        logger.debug(
            "Selected source candidate | "
            "score=%s | url=%s | text=%s",
            best_score,
            best_link,
            best_text,
        )

        return best_link

    # ------------------------------------------------------------------

    def _score_candidate(
        self,
        link: str,
        link_text: str,
        page_context: str,
    ):

        lower_link = link.lower()

        lower_text = (link_text or "").lower()

        combined = lower_link + " " + lower_text

        score = 0

        is_pdf = self._is_pdf(lower_link)

        # --------------------------------------------------------------
        # PDF BASE SCORE
        # --------------------------------------------------------------

        if is_pdf:
            score += 35

        # --------------------------------------------------------------
        # TENDER RELEVANCE
        # --------------------------------------------------------------

        tender_matches = 0

        for keyword in self.TENDER_KEYWORDS:
            if keyword in combined:
                tender_matches += 1

        score += min(
            tender_matches * 12,
            60,
        )

        # --------------------------------------------------------------
        # LINK TEXT QUALITY
        # --------------------------------------------------------------

        if lower_text:
            if any(
                keyword in lower_text
                for keyword in (
                    "download",
                    "tender document",
                    "tender notice",
                    "nit",
                    "rfp",
                    "eoi",
                    "bid document",
                    "corrigendum",
                    "empanelment",
                )
            ):
                score += 25

        # --------------------------------------------------------------
        # OFFICIAL DOMAIN
        # --------------------------------------------------------------

        if any(
            domain in lower_link
            for domain in self.GOV_DOMAINS
        ):
            score += 15

        # --------------------------------------------------------------
        # DOCUMENT INDICATORS
        # --------------------------------------------------------------

        if any(
            keyword in lower_link
            for keyword in self.PDF_KEYWORDS
        ):
            score += 10

        # --------------------------------------------------------------
        # IRRELEVANT DOCUMENT PENALTY
        # --------------------------------------------------------------

        irrelevant_matches = 0

        for keyword in self.IRRELEVANT_DOCUMENT_KEYWORDS:
            if keyword in combined:
                irrelevant_matches += 1

        if irrelevant_matches:
            score -= irrelevant_matches * 60

        # --------------------------------------------------------------
        # SAME-SITE CONTEXT
        # --------------------------------------------------------------

        page_domain = urlparse(
            page_context
        ).netloc.lower()

        link_domain = urlparse(
            link
        ).netloc.lower()

        if (
            page_domain
            and link_domain
            and page_domain == link_domain
        ):
            score += 10

        # --------------------------------------------------------------
        # EXTERNAL DOCUMENT SAFETY
        # --------------------------------------------------------------

        if (
            is_pdf
            and page_domain
            and link_domain
            and page_domain != link_domain
            and tender_matches < 2
        ):
            score -= 40

        return score

    # ------------------------------------------------------------------

    def _build_page_context(
        self,
        page_url: str,
    ) -> str:

        return page_url or ""

    # ------------------------------------------------------------------

    def _normalize(
        self,
        url: str,
    ) -> str:

        try:
            parsed = urlparse(url)

            cleaned = parsed._replace(
                fragment=""
            )

            return cleaned.geturl()

        except Exception:
            return url

    # ------------------------------------------------------------------

    def _is_pdf(
        self,
        url: str,
    ) -> bool:

        lower = (url or "").lower()

        return (
            lower.endswith(".pdf")
            or ".pdf?" in lower
            or "/pdf/" in lower
            or "application/pdf" in lower
        )

    # ------------------------------------------------------------------

    def _is_html(
        self,
        response: requests.Response,
    ) -> bool:

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        return "text/html" in content_type