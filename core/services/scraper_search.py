import re
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

import requests
from bs4 import BeautifulSoup

from config.official_sources import OFFICIAL_SOURCES
from utils.logger import logger


class ScraperSearch:
    """
    Discover tender opportunities directly from official websites.

    Responsibilities
    ----------------
    - Visit configured official procurement sources
    - Discover real procurement/navigation pages instead of blindly
      guessing URL paths
    - Crawl a controlled number of relevant same-domain pages
    - Identify promising tender/opportunity links
    - Reject obvious navigation, login, result, career, investor,
      corporate, and unrelated pages
    - Return candidate tender URLs

    This complements SERP search by crawling official sources directly.

    Important
    ---------
    ScraperSearch is a DISCOVERY layer.

    It should return promising candidate URLs, not fully parsed tenders.
    Detailed extraction is handled later by TenderExtractionEngine.
    """

    REQUEST_TIMEOUT = 10

    MAX_SOURCES_PER_SEARCH = 15

    MAX_PAGES_PER_SOURCE = 12

    MAX_CANDIDATES_PER_SOURCE = 25

    MAX_NAVIGATION_LINKS_PER_SOURCE = 12

    MAX_CRAWL_DEPTH = 2

    # Maximum amount of local DOM context allowed to influence candidate
    # relevance. This prevents a huge page-level container from injecting
    # unrelated words such as "tender" into every link on the page.
    MAX_LOCAL_CONTEXT_LENGTH = 1200

    # Very generic anchor labels should never become the title unless
    # meaningful surrounding row/list context exists.
    GENERIC_ANCHOR_TEXTS = {
        "view",
        "details",
        "detail",
        "click here",
        "click",
        "download",
        "more",
        "read more",
        "open",
        "document",
        "view details",
        "view document",
        "download document",
    }

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/138.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,"
            "application/xhtml+xml,"
            "application/xml;q=0.9,"
            "*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    # ------------------------------------------------------------------
    # Procurement / tender navigation signals
    # ------------------------------------------------------------------

    PROCUREMENT_NAV_KEYWORDS = [
        "tender",
        "tenders",
        "procurement",
        "eprocurement",
        "e-procurement",
        "e-tender",
        "etender",
        "e-tendering",
        "bid",
        "bids",
        "bidding",
        "bid invitation",
        "rfp",
        "rfq",
        "eoi",
        "expression of interest",
        "notice inviting tender",
        "invitation for bids",
        "invitation to bid",
        "request for proposal",
        "request for quotation",
        "consultancy",
        "consultant",
        "empanelment",
        "notices",
        "procurement notice",
        "business opportunities",
        "vendor",
        "contracts",
    ]

    # ------------------------------------------------------------------
    # Positive procurement / opportunity language
    # ------------------------------------------------------------------

    TENDER_KEYWORDS = [
        "tender",
        "tenders",
        "rfp",
        "rfq",
        "eoi",
        "expression of interest",
        "notice inviting tender",
        "invitation for bids",
        "invitation to bid",
        "request for proposal",
        "request for quotation",
        "bid invitation",
        "bidding",
        "empanelment",
        "consultant",
        "consultancy",
        "structural",
        "structural consultant",
        "structural consultancy",
        "structural engineer",
        "structural engineering",
        "structural audit",
        "proof checking",
        "peer review",
        "retrofitting",
        "rehabilitation",
        "design consultant",
        "engineering consultant",
    ]

    # ------------------------------------------------------------------
    # Strong negative URL patterns
    # ------------------------------------------------------------------

    BAD_LINK_PATTERNS = [
        "login",
        "signin",
        "sign-in",
        "register",
        "registration",
        "contact",
        "privacy",
        "terms",
        "about",
        "career",
        "careers",
        "recruitment",
        "vacancy",
        "jobs",
        "apprentice",
        "apprenticeship",
        "news",
        "gallery",
        "facebook",
        "twitter",
        "linkedin",
        "youtube",
        "instagram",
        "vendor-registration",
        "vendor_registration",
        "vendorregistration",
        "buyer-registration",
        "buyer_registration",
        "buyerregistration",
        "bidder-registration",
        "bidder_registration",
        "bidderregistration",
        "bidder-login",
        "buyer-login",
        "bid-result",
        "bidresult",
        "bid-result-list",
        "bidresultlists",
        "result-list",
        "results",
        "statistics",
        "statistic",
        "dashboard",
        "reports",
        "report",
        "analytics",
        "archive",
        "archived",
        "sitemap",
        "slideshare",
        "investor",
        "investors",
        "shareholder",
        "annual-report",
        "annualreport",
        "financial-results",
        "financial-result",
        "stock-exchange",
        "corporate",
        "press-release",
        "pressrelease",
        "media",
        "events",
        "event",
        "pay",
        "citizen",
    ]

    # ------------------------------------------------------------------
    # URL/query patterns that are normally navigation/sorting controls.
    # ------------------------------------------------------------------

    BAD_QUERY_PATTERNS = [
        "order_by=",
        "sort=",
        "orderby=",
        "sortby=",
        "page=",
        "pageno=",
        "page_no=",
        "offset=",
        "limit=",
        "filter=",
        "filterby=",
        "search=",
        "keyword=",
        "orderby",
    ]

    # ------------------------------------------------------------------
    # Generic navigation titles that should not become opportunities
    # ------------------------------------------------------------------

    BAD_TITLE_PATTERNS = [
        "buyer registration",
        "bidder registration",
        "vendor registration",
        "vendor login",
        "buyer login",
        "bidder login",
        "ongoing bids",
        "bid/ra status",
        "bid status",
        "bid result",
        "bid results",
        "list of bids",
        "procurement data",
        "procurement statistics",
        "procurement report",
        "dashboard",
        "login",
        "registration",
        "contact us",
        "about us",
        "career",
        "careers",
        "recruitment",
        "apprentice",
        "apprenticeship",
        "privacy policy",
        "terms and conditions",
        "organisation name",
        "organization name",
        "tender opening date",
        "bid submission closing date",
        "e-published date",
        "title/ref.no./tender id",
        "corrigendum",
        "download",
        "details",
        "click here",
    ]

    # ------------------------------------------------------------------
    # Query terms indicating relevance to Livehooah
    # ------------------------------------------------------------------

    RELEVANCE_KEYWORDS = [
        "structural",
        "structural consultant",
        "structural consultancy",
        "structural engineer",
        "structural engineering",
        "structural design",
        "structural analysis",
        "structural audit",
        "proof checking",
        "proof check",
        "peer review",
        "retrofitting",
        "rehabilitation",
        "consultant",
        "consultancy",
        "empanelment",
        "engineering consultancy",
        "engineering consultant",
        "design consultant",
    ]

    WEAK_GENERIC_TERMS = [
        "consultant",
        "consultancy",
        "empanelment",
        "eoi",
        "expression of interest",
    ]

    STRONG_RELEVANCE_KEYWORDS = [
        "structural",
        "structural consultant",
        "structural consultancy",
        "structural engineer",
        "structural engineering",
        "structural design",
        "structural analysis",
        "structural audit",
        "proof checking",
        "proof check",
        "peer review",
        "retrofitting",
        "rehabilitation",
        "engineering consultant",
        "engineering consultancy",
        "design consultant",
    ]

    OPPORTUNITY_EVIDENCE_KEYWORDS = [
        "tender id",
        "tender no",
        "tender number",
        "tender ref",
        "reference no",
        "ref no",
        "notice no",
        "notice number",
        "bid no",
        "bid number",
        "bid reference",
        "submission date",
        "submission deadline",
        "bid submission",
        "closing date",
        "closing time",
        "last date",
        "last date for submission",
        "due date",
        "opening date",
        "tender opening",
        "bid opening",
        "estimated cost",
        "emd",
        "earnest money",
        "document fee",
        "scope of work",
        "scope of services",
        "terms of reference",
        "tor",
        "invitation",
    ]

    DOCUMENT_EXTENSIONS = (
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
    )

    def __init__(self):
        self.sources = OFFICIAL_SOURCES

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def _normalize_query(self, query: str):
        if not query:
            return []

        return [
            token.strip().lower()
            for token in re.findall(
                r"[a-zA-Z0-9]+",
                query,
            )
            if token.strip()
        ]

    def _query_phrases(self, query: str):
        normalized = " ".join(
            self._normalize_query(query)
        )

        phrases = []

        if normalized:
            phrases.append(normalized)

        known_phrases = [
            "structural consultant",
            "structural consultancy",
            "structural engineer",
            "structural engineering",
            "structural audit",
            "proof checking",
            "peer review",
            "retrofitting",
            "engineering consultant",
            "engineering consultancy",
            "consultant empanelment",
            "consultancy empanelment",
        ]

        for phrase in known_phrases:
            if phrase in normalized:
                phrases.append(phrase)

        return list(dict.fromkeys(phrases))

    # ------------------------------------------------------------------
    # Source handling
    # ------------------------------------------------------------------

    def _flatten_sources(self):
        urls = []

        for category in self.sources.values():

            for source in category:

                if isinstance(source, str):
                    urls.append(source)

                elif isinstance(source, dict):

                    url = source.get("url")

                    if url:
                        urls.append(url)

        return urls

    def _score_source(
        self,
        query_tokens,
        source: dict,
    ):
        score = 0.0

        searchable_fields = [
            source.get("category", ""),
            *source.get("keywords", []),
            *source.get("services", []),
            *source.get("sectors", []),
        ]

        searchable_text = " ".join(
            str(item).lower()
            for item in searchable_fields
        )

        for token in query_tokens:

            if token in searchable_text:
                score += 2

        priority = source.get(
            "priority",
            0,
        )

        try:
            score += float(priority) * 0.5
        except (TypeError, ValueError):
            pass

        return score

    def _select_sources(self, query: str):
        query_tokens = self._normalize_query(query)

        scored_sources = []

        for category_sources in self.sources.values():

            for source in category_sources:

                if not isinstance(source, dict):
                    continue

                score = self._score_source(
                    query_tokens,
                    source,
                )

                if score > 0:
                    scored_sources.append(
                        (
                            score,
                            source,
                        )
                    )

        scored_sources.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        selected = [
            source
            for _, source in scored_sources[
                : self.MAX_SOURCES_PER_SEARCH
            ]
        ]

        if not selected:

            logger.debug(
                "No source matched query '%s'. "
                "Using default official sources.",
                query,
            )

            selected = [
                source
                for category in self.sources.values()
                for source in category
                if isinstance(source, dict)
            ][: self.MAX_SOURCES_PER_SEARCH]

        logger.debug(
            "Selected %d official sources for '%s'",
            len(selected),
            query,
        )

        return selected

    # ------------------------------------------------------------------
    # URL handling
    # ------------------------------------------------------------------

    def _normalize_url(
        self,
        url: str,
    ):
        if not url:
            return ""

        url = url.strip()

        url, _ = urldefrag(url)

        parsed = urlparse(url)

        if parsed.scheme not in {
            "http",
            "https",
        }:
            return ""

        if not parsed.netloc:
            return ""

        path = re.sub(
            r"/{2,}",
            "/",
            parsed.path,
        )

        normalized = parsed._replace(
            path=path,
        ).geturl()

        return normalized.rstrip("/")

    def _same_domain(
        self,
        url: str,
        base_url: str,
    ):
        return (
            urlparse(url).netloc.lower()
            == urlparse(base_url).netloc.lower()
        )

    def _is_document_url(
        self,
        url: str,
    ):
        if not url:
            return False

        path = urlparse(url).path.lower()

        return any(
            extension in path
            for extension in self.DOCUMENT_EXTENSIONS
        )

    def _has_bad_query_pattern(
        self,
        url: str,
    ):
        """
        Reject URLs that are clearly sorting/filter/navigation controls.

        This is particularly important for GeM, where URLs such as:

            /cppp?order_by=cdate&type=asc

        are navigation controls rather than individual tenders.
        """

        parsed = urlparse(url)

        query = parsed.query.lower()

        return any(
            pattern in query
            for pattern in self.BAD_QUERY_PATTERNS
        )

    # ------------------------------------------------------------------
    # Procurement navigation scoring
    # ------------------------------------------------------------------

    def _procurement_navigation_score(
        self,
        text: str,
        url: str,
    ):
        combined = " ".join(
            str(value).lower()
            for value in (
                text,
                url,
            )
        )

        score = 0

        for keyword in self.PROCUREMENT_NAV_KEYWORDS:

            if keyword in combined:
                score += 1

        path = urlparse(url).path.lower()

        strong_path_terms = [
            "tender",
            "procurement",
            "eprocurement",
            "e-procurement",
            "rfp",
            "rfq",
            "eoi",
            "bid",
            "bidding",
            "consultancy",
            "empanelment",
            "notice",
        ]

        for term in strong_path_terms:

            if term in path:
                score += 2

        return score

    def _discover_navigation_links(
        self,
        html: str,
        base_url: str,
    ):
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        candidates = []

        seen = set()

        for link in soup.find_all(
            "a",
            href=True,
        ):

            href = link.get("href")

            if not href:
                continue

            absolute = self._normalize_url(
                urljoin(
                    base_url,
                    href,
                )
            )

            if not absolute:
                continue

            if not self._same_domain(
                absolute,
                base_url,
            ):
                continue

            if absolute in seen:
                continue

            if self._is_document_url(absolute):
                continue

            text = link.get_text(
                " ",
                strip=True,
            )

            if self._is_bad_url(absolute):
                normalized_absolute = absolute.lower()

                procurement_archive_signal = (
                    "archive" in normalized_absolute
                    and self._procurement_navigation_score(
                    text,
                    absolute,
                ) > 0
            )

                if not procurement_archive_signal:
                    continue

            if self._has_bad_query_pattern(absolute):
                continue

            if self._is_bad_title(text):
                continue

            score = self._procurement_navigation_score(
                text,
                absolute,
            )

            if score <= 0:
                continue

            seen.add(absolute)

            candidates.append(
                (
                    score,
                    absolute,
                    text,
                )
            )

        candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return candidates[
            : self.MAX_NAVIGATION_LINKS_PER_SOURCE
        ]

    # ------------------------------------------------------------------
    # Fetching
    # ------------------------------------------------------------------

    def _fetch_page(
        self,
        url: str,
    ):
        logger.debug(
            "Fetching scraper page: %s",
            url,
        )

        try:

            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=self.REQUEST_TIMEOUT,
                allow_redirects=True,
            )

            if response.status_code != 200:

                logger.debug(
                    "Scraper skipped page | url=%s | status=%s",
                    url,
                    response.status_code,
                )

                return None

            content_type = response.headers.get(
                "Content-Type",
                "",
            ).lower()

            if (
                "text/html" not in content_type
                and "application/xhtml+xml" not in content_type
            ):

                logger.debug(
                    "Scraper skipped non-HTML page | "
                    "url=%s | content_type=%s",
                    url,
                    content_type,
                )

                return None

            return response.text

        except requests.RequestException as exc:

            logger.debug(
                "Scraper request failed | url=%s | error=%s",
                url,
                exc,
            )

            return None

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _is_bad_url(
        self,
        url: str,
    ):    
        if not url:
            return True

        normalized = url.lower()

        if self._has_bad_query_pattern(url):
            return True

        parsed = urlparse(url)

        path = parsed.path.lower()

        # --------------------------------------------------------------
        # Archive URLs need special handling.
        #
        # A legitimate tender document can be stored inside an archive
        # directory, for example:
        #
        #   /public/storage/tenders_archives/NIT_1782387339.pdf
        #
        # The generic "archive" BAD_LINK_PATTERN must not reject such
        # documents merely because the directory name contains
        # "archive".
        #
        # Actual archive/navigation pages remain rejectable.
        # --------------------------------------------------------------
        if self._is_document_url(url):
            non_archive_patterns = [
                pattern
                for pattern in self.BAD_LINK_PATTERNS
                if pattern not in (
                    "archive",
                    "archived",
                )
            ]

            return any(
                pattern in normalized
                for pattern in non_archive_patterns
            )

        return any(
            pattern in normalized
            for pattern in self.BAD_LINK_PATTERNS
        )

    def _is_bad_title(
        self,
        title: str,
    ):
        normalized = " ".join(
            title.lower().split()
        )

        if not normalized:
            return False

        for pattern in self.BAD_TITLE_PATTERNS:

            pattern_normalized = " ".join(
                pattern.lower().split()
            )

            if not pattern_normalized:
                continue

            # ----------------------------------------------------------
            # Short navigation terms must match as complete words.
            #
            # Example:
            #   "view" must reject "View Details"
            #   but must NOT reject "Peer Review".
            # ----------------------------------------------------------

            if len(pattern_normalized) <= 4:
                if re.search(
                    rf"\b{re.escape(pattern_normalized)}\b",
                    normalized,
                ):
                    return True

                continue

            if pattern_normalized in normalized:
                return True

        return False

    def _query_relevance_score(
        self,
        text: str,
        query: str,
    ):
        searchable = " ".join(
            text.lower().split()
        )

        query_tokens = self._normalize_query(
            query
        )

        score = 0

        for token in query_tokens:

            if len(token) < 3:
                continue

            if token in searchable:
                score += 1

        for phrase in self._query_phrases(
            query
        ):

            if len(phrase) >= 5 and phrase in searchable:
                score += 3

        return score

    def _structural_relevance_score(
        self,
        text: str,
    ):
        searchable = " ".join(
            text.lower().split()
        )

        score = 0

        for keyword in self.STRONG_RELEVANCE_KEYWORDS:

            if keyword in searchable:
                score += 2

        return score

    def _opportunity_evidence_score(
        self,
        text: str,
    ):
        searchable = " ".join(
            text.lower().split()
        )

        score = 0

        for keyword in self.OPPORTUNITY_EVIDENCE_KEYWORDS:

            if keyword in searchable:
                score += 1

        return score

    def _candidate_score(
        self,
        text: str,
        url: str,
        query: str,
        page_context: str = "",
    ):
        combined = " ".join(
            value
            for value in (
                text,
                url,
                page_context,
            )
            if value
        )

        searchable = " ".join(
            combined.lower().split()
        )

        score = 0

        score += self._query_relevance_score(
            searchable,
            query,
        )

        score += self._structural_relevance_score(
            searchable,
        )

        for keyword in self.TENDER_KEYWORDS:

            if keyword in searchable:
                score += 1

        strong_procurement_terms = [
            "tender",
            "rfp",
            "rfq",
            "eoi",
            "expression of interest",
            "notice inviting tender",
            "invitation for bids",
            "request for proposal",
            "empanelment",
        ]

        for keyword in strong_procurement_terms:

            if keyword in searchable:
                score += 2

        score += self._opportunity_evidence_score(
            searchable
        )

        if self._is_document_url(url):
            score += 2

        return score

    def _has_strong_structural_signal(
        self,
        text: str,
    ):
        searchable = " ".join(
            text.lower().split()
        )

        return any(
            keyword in searchable
            for keyword in self.STRONG_RELEVANCE_KEYWORDS
        )

    def _strong_structural_signal_count(
        self,
        text: str,
    ):
        searchable = " ".join(
            text.lower().split()
        )

        return sum(
            1
            for keyword in self.STRONG_RELEVANCE_KEYWORDS
            if keyword in searchable
        )

    def _has_strong_procurement_signal(
        self,
        text: str,
    ):
        searchable = " ".join(
            text.lower().split()
        )

        strong_terms = [
            "tender",
            "rfp",
            "rfq",
            "eoi",
            "expression of interest",
            "notice inviting tender",
            "invitation for bids",
            "request for proposal",
            "empanelment",
            "bid invitation",
        ]

        return any(
            keyword in searchable
            for keyword in strong_terms
        )

    def _looks_like_tender_link(
        self,
        text: str,
        url: str,
        query: str,
        page_context: str = "",
    ):
        if not url:
            return False

        if self._is_bad_url(url):
            return False

        if self._is_bad_title(text):
            return False

        combined = " ".join(
            value
            for value in (
                text,
                url,
                page_context,
            )
            if value
        ).lower()

        procurement_signal = any(
            keyword in combined
            for keyword in self.TENDER_KEYWORDS
        )

        structural_signal = (
            self._has_strong_structural_signal(
                combined
            )
        )

        strong_procurement_signal = (
            self._has_strong_procurement_signal(
                combined
            )
        )

        query_signal = (
            self._query_relevance_score(
                combined,
                query,
            )
            > 0
        )

        opportunity_evidence = (
            self._opportunity_evidence_score(
                combined
            )
            > 0
        )

        document_signal = self._is_document_url(
            url
        )

        # --------------------------------------------------------------
        # Generic navigation protection.
        # --------------------------------------------------------------

        normalized_title = " ".join(
            text.lower().split()
        )

        if (
            normalized_title
            in self.GENERIC_ANCHOR_TEXTS
            and not page_context
        ):
            return False

        # --------------------------------------------------------------
        # Generic pages without meaningful opportunity evidence.
        # --------------------------------------------------------------

        generic_only = (
            procurement_signal
            and not structural_signal
            and not opportunity_evidence
            and not query_signal
            and not document_signal
        )

        if generic_only:
            return False

        # Candidate score.
        # --------------------------------------------------------------
        # --------------------------------------------------------------

        score = self._candidate_score(
            text,
            url,
            query,
            page_context,
        )

        # --------------------------------------------------------------
        # Documents require actual Livehooah relevance.
        #
        # A document being:
        #   - a PDF,
        #   - linked from a tender page,
        #   - a tender,
        #   - or containing procurement metadata
        #
        # is NOT enough.
        #
        # This prevents unrelated procurement documents such as:
        #   - canteen tenders
        #   - housekeeping tenders
        #   - laboratory equipment
        #   - manpower supply
        #   - routine maintenance
        #
        # from becoming scraper candidates.
        # --------------------------------------------------------------

        if document_signal:

            strong_structural_count = (
                self._strong_structural_signal_count(
                    combined
                )
            )

            if (
                structural_signal
                and (
                    strong_procurement_signal
                    or opportunity_evidence
                )
                and score >= 5
            ):
                return True

            if (
                strong_structural_count >= 2
                and score >= 10
            ):
                return True

            return False

        # --------------------------------------------------------------
        # Non-document pages.
        #
        # Generic consultant / consultancy / empanelment / EOI pages
        # are not enough by themselves.
        # --------------------------------------------------------------

        if structural_signal and strong_procurement_signal:
            return True

        if structural_signal and opportunity_evidence:
            return True

        # Query overlap alone must not qualify a candidate.
        #
        # This prevents generic terms such as "consultant",
        # "consultancy", "EOI", etc. from causing false positives.
        # --------------------------------------------------------------

        return False

    # ------------------------------------------------------------------
    # Link context extraction
    # ------------------------------------------------------------------

    def _clean_context(
        self,
        text: str,
    ):
        if not text:
            return ""

        normalized = " ".join(
            text.split()
        )

        if len(normalized) > self.MAX_LOCAL_CONTEXT_LENGTH:
            normalized = normalized[
                : self.MAX_LOCAL_CONTEXT_LENGTH
            ]

        return normalized

    def _extract_link_context(
        self,
        link,
        page_title: str,
    ):
        """
        Extract ONLY local procurement context.

        Important:
        We deliberately do not include the entire page title or large
        ancestor containers. Doing so caused unrelated CPWD/ONGC/GeM
        links to inherit procurement keywords from the surrounding page.
        """

        contexts = []

        anchor_text = link.get_text(
            " ",
            strip=True,
        )

        if anchor_text:
            contexts.append(
                anchor_text
            )

        # --------------------------------------------------------------
        # Table row is the strongest context for procurement portals.
        # --------------------------------------------------------------

        row = link.find_parent("tr")

        if row:
            row_text = row.get_text(
                " ",
                strip=True,
            )

            if row_text:
                contexts.append(
                    row_text
                )

        # --------------------------------------------------------------
        # List item is the second strongest context.
        # --------------------------------------------------------------

        list_item = link.find_parent("li")

        if list_item:
            li_text = list_item.get_text(
                " ",
                strip=True,
            )

            if li_text:
                contexts.append(
                    li_text
                )

        # --------------------------------------------------------------
        # Generic parent only if it is genuinely local.
        #
        # Never walk multiple arbitrary ancestors.
        # --------------------------------------------------------------

        parent = link.parent

        if parent:

            parent_text = parent.get_text(
                " ",
                strip=True,
            )

            if parent_text:
                cleaned = self._clean_context(
                    parent_text
                )

                if cleaned:
                    contexts.append(
                        cleaned
                    )

        # --------------------------------------------------------------
        # Deduplicate and avoid giant blocks.
        # --------------------------------------------------------------

        cleaned_contexts = []

        seen = set()

        for context in contexts:

            normalized = self._clean_context(
                context
            )

            if not normalized:
                continue

            if normalized in seen:
                continue

            seen.add(normalized)

            cleaned_contexts.append(
                normalized
            )

        return " | ".join(
            cleaned_contexts
        )

    # ------------------------------------------------------------------
    # Link extraction
    # ------------------------------------------------------------------

    def _extract_links(
        self,
        html,
        base_url,
        query,
    ):
        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        opportunities = []

        seen = set()

        base_domain = urlparse(
            base_url
        ).netloc.lower()

        for link in soup.find_all(
            "a",
            href=True,
        ):

            href = link.get("href")

            if not href:
                continue

            absolute = self._normalize_url(
                urljoin(
                    base_url,
                    href,
                )
            )

            if not absolute:
                continue

            parsed = urlparse(
                absolute
            )

            candidate_domain = parsed.netloc.lower()

            if not (
                candidate_domain == base_domain
                or candidate_domain.endswith("." + base_domain)
            ):
                continue

            if absolute in seen:
                continue

            if self._is_bad_url(absolute):
                continue

            text = link.get_text(
                " ",
                strip=True,
            )

            if self._is_bad_title(text):
                continue

            local_context = self._extract_link_context(
                link,
                "",
            )

            if not self._looks_like_tender_link(
                text,
                absolute,
                query,
                local_context,
            ):
                continue

            score = self._candidate_score(
                text,
                absolute,
                query,
                local_context,
            )

            seen.add(
                absolute
            )

            title = (
                text
                or absolute.rstrip(
                    "/"
                ).split("/")[-1]
            )

            generic_anchor = (
                not text
                or text.strip().lower()
                in self.GENERIC_ANCHOR_TEXTS
            )

            if generic_anchor:

                row = link.find_parent("tr")

                if row:
                    row_text = row.get_text(
                        " ",
                        strip=True,
                    )

                    if row_text:
                        title = row_text[:500]

                else:

                    list_item = link.find_parent("li")

                    if list_item:
                        li_text = list_item.get_text(
                            " ",
                            strip=True,
                        )

                        if li_text:
                            title = li_text[:500]

            opportunities.append(
                {
                    "title": title,
                    "description": local_context[:1500],
                    "source_url": absolute,
                    "organization": "",
                    "location": "",
                    "_scraper_score": score,
                }
            )

            if (
                len(opportunities)
                >= self.MAX_CANDIDATES_PER_SOURCE
            ):
                break

        opportunities.sort(
            key=lambda item: item.get(
                "_scraper_score",
                0,
            ),
            reverse=True,
        )

        return opportunities

    # ------------------------------------------------------------------
    # Controlled crawling
    # ------------------------------------------------------------------

    def _crawl_source(
        self,
        source_url: str,
        query: str,
    ):
        base_url = self._normalize_url(
            source_url
        )

        if not base_url:
            return [], 0

        queue = deque()

        queue.append(
            (
                base_url,
                0,
            )
        )

        queued = {
            base_url
        }

        fetched = set()

        opportunities = []

        seen_opportunity_urls = set()

        while queue:

            if len(fetched) >= self.MAX_PAGES_PER_SOURCE:
                break

            current_url, depth = queue.popleft()

            if current_url in fetched:
                continue

            if self._is_document_url(
                current_url
            ):
                continue

            fetched.add(
                current_url
            )

            html = self._fetch_page(
                current_url
            )

            if not html:
                continue

            candidates = self._extract_links(
                html,
                current_url,
                query,
            )

            for opportunity in candidates:

                url = opportunity.get(
                    "source_url"
                )

                if not url:
                    continue

                if url in seen_opportunity_urls:
                    continue

                seen_opportunity_urls.add(
                    url
                )

                opportunities.append(
                    opportunity
                )

                if (
                    len(opportunities)
                    >= self.MAX_CANDIDATES_PER_SOURCE
                ):
                    break

            if (
                len(opportunities)
                >= self.MAX_CANDIDATES_PER_SOURCE
            ):
                break

            if depth >= self.MAX_CRAWL_DEPTH:
                continue

            navigation_links = self._discover_navigation_links(
                html,
                current_url,
            )

            for _, link_url, link_text in navigation_links:

                if link_url in queued:
                    continue

                if link_url in fetched:
                    continue

                if self._is_bad_url(
                    link_url
                ):
                    normalized_link_url = link_url.lower()

                    procurement_archive_signal = (
                    "archive" in normalized_link_url
                        and self._procurement_navigation_score(
                        link_text,
                        link_url,
                    ) > 0
                )

                    if not procurement_archive_signal:
                        continue

                if self._is_document_url(
                    link_url
                ):
                    continue

                queued.add(
                    link_url
                )

                queue.append(
                    (
                        link_url,
                        depth + 1,
                    )
                )

                logger.debug(
                    "Scraper discovered procurement page | "
                    "source=%s | depth=%d | title=%s | url=%s",
                    base_url,
                    depth + 1,
                    link_text,
                    link_url,
                )

                if (
                    len(queue)
                    + len(fetched)
                    >= self.MAX_PAGES_PER_SOURCE
                ):
                    break

        logger.debug(
            "Scraper source completed | "
            "source=%s | pages=%d | candidates=%d",
            base_url,
            len(fetched),
            len(opportunities),
        )

        return opportunities, len(fetched)

    # ------------------------------------------------------------------
    # Candidate URL compatibility helper
    # ------------------------------------------------------------------

    def _candidate_urls(self, query: str):
        selected_sources = self._select_sources(
            query
        )

        candidates = []

        for source in selected_sources:

            base = self._normalize_url(
                source.get(
                    "url",
                    "",
                )
            )

            if not base:
                continue

            candidates.append(
                base
            )

        return list(
            dict.fromkeys(
                candidates
            )
        )

    # ------------------------------------------------------------------
    # Main search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
    ):
        logger.info(
            "Scraper search started | query=%s",
            query,
        )

        opportunities = []

        seen_urls = set()

        selected_sources = self._select_sources(
            query
        )

        sources_processed = 0

        pages_fetched = 0

        for source in selected_sources:

            source_url = self._normalize_url(
                source.get(
                    "url",
                    "",
                )
            )

            if not source_url:
                continue

            sources_processed += 1

            source_opportunities, source_pages_fetched = (
                self._crawl_source(
                    source_url,
                    query,
                )
            )

            pages_fetched += source_pages_fetched

            for opportunity in source_opportunities:

                url = opportunity.get(
                    "source_url"
                )

                if not url:
                    continue

                if url in seen_urls:
                    continue

                seen_urls.add(
                    url
                )

                opportunity.pop(
                    "_scraper_score",
                    None,
                )

                opportunities.append(
                    opportunity
                )

        logger.info(
            "Scraper search completed | "
            "query=%s | sources=%d | pages_fetched=%d | candidates=%d",
            query,
            sources_processed,
            pages_fetched,
            len(opportunities),
        )

        return opportunities