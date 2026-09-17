import logging
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from core.services.serp_search import SerpSearch
from core.services.scraper_search import ScraperSearch
from core.services.tender_intelligence import TenderIntelligence

logger = logging.getLogger(__name__)


# ==========================================================
# AGGREGATOR / LOW-QUALITY SOURCE BLOCKLIST
# ==========================================================

PORTAL_BLOCKLIST = [
    "bidassist",
    "tendersinfo",
    "tenderdetail",
    "tendernews",
    "tender247",
    "tenderbazaar",
    "justdial",
    "indiamart",
    "sulekha",
]


# ==========================================================
# GENERIC OPPORTUNITY SIGNALS
# ==========================================================

TENDER_KEYWORDS = [
    "tender",
    "tenders",
    "rfp",
    "request for proposal",
    "rfq",
    "request for quotation",
    "eoi",
    "expression of interest",
    "empanelment",
    "bid",
    "bidding",
    "corrigendum",
    "invitation for bids",
    "notice inviting tender",
]

# ==========================================================
# STRONG LIVEHOOAH RELEVANCE SIGNALS
#
# These are used only for pre-extraction discovery filtering.
# Final scoring remains the responsibility of
# compute_livehooah_score().
# ==========================================================

STRONG_RELEVANCE_KEYWORDS = [
    "structural engineering",
    "structural consultancy",
    "structural consultant",
    "structural consultants",
    "structural engineer",
    "structural engineers",
    "structural design",
    "structural analysis",
    "proof checking",
    "proof check",
    "peer review",
    "structural audit",
    "retrofit",
    "retrofitting",
    "rehabilitation",
    "structural health monitoring",
    "design and drawings",
    "structural drawings",
    "civil structural",
    "rcc design",
    "steel structure",
    "steel structures",
    "pre-engineered building",
    "pre engineered building",
    "peb structure",
    "peb structures",
    "industrial structure",
    "industrial structures",
    "industrial shed",
    "industrial sheds",
    "warehouse",
    "warehouses",
    "logistics park",
    "logistics hub",
    "high-rise",
    "high rise",
    "residential tower",
    "residential towers",
    "commercial tower",
    "commercial towers",
    # --- Additional consultancy-adjacent signals ---
    "third party inspection",
    "structural assessment",
    "condition survey",
    "due diligence",
    "forensic engineering",
    "value engineering",
    "independent engineer",
    "owner's engineer",
    "owners engineer",
    "detailed engineering",
    "design review",
    "authority engineer",
    "bridge inspection",
    "seismic evaluation",
    "vulnerability assessment",
    "rehabilitation design",
]


# ==========================================================
# SUPPORTING CONSULTANCY SIGNALS
# ==========================================================

CONSULTANCY_KEYWORDS = [
    "consultant",
    "consultants",
    "consultancy",
    "consultancy services",
    "engineering services",
    "design services",
    "structural services",
    "proof checking",
    "peer review",
    "structural audit",
    "empanelment of consultants",
    "empanelment of consultant",
    "selection of consultant",
    "selection of consultants",
    "appointment of consultant",
    "appointment of consultants",
    "technical consultancy",
]


# ==========================================================
# CLEARLY UNRELATED SERVICE SIGNALS
#
# These should not automatically reject every result.
# A result containing one of these terms can still be retained
# when it also contains strong structural consultancy signals.
# ==========================================================

UNRELATED_SERVICE_KEYWORDS = [
    "landscaping",
    "landscape maintenance",
    "tree cutting",
    "tree plantation",
    "gardening",
    "horticulture",
    "demolition",
    "demolition work",
    "hvac maintenance",
    "air conditioning maintenance",
    "housekeeping",
    "sanitation",
    "sweeping",
    "cleaning services",
    "janitorial",
    "restaurant",
    "catering",
    "food services",
    "security services",
    "manpower supply",
    "electrical maintenance",
    "facility management",
    "pest control",
]


# ==========================================================
# URL / PAGE PATTERNS
# ==========================================================

BAD_URL_PATTERNS = [
    "/category/",
    "/categories/",
    "/search",
    "/tag/",
    "/tags/",
    "page=",
    "/login",
    "/signin",
    "/sign-in",
]


TENDER_URL_HINTS = [
    "/tender",
    "/tenders",
    "/procurement",
    "/rfp",
    "/eoi",
    "/bid",
    "/bids",
    "/empanelment",
    "/notice",
]


# ==========================================================
# URL CANONICALIZATION
# ==========================================================

# Exact-match tracking parameters to strip during deduplication.
TRACKING_PARAMS = {
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "igshid",
    "spm",
}

# Prefixes for tracking parameters (e.g. utm_source, utm_medium, ...).
TRACKING_PARAM_PREFIXES = ("utm_",)


# ==========================================================
# DISCOVERY SCORING
# ==========================================================

# Opportunities scoring below this threshold are dropped before
# extraction, regardless of whether they technically pass the
# minimum relevance checks.
MIN_DISCOVERY_SCORE = 10


class SearchRouter:

    def __init__(self):

        self.serp_search = SerpSearch()
        self.scraper_search = ScraperSearch()
        self.intelligence = TenderIntelligence()

    # ======================================================
    # TEXT MATCHING HELPERS
    # ======================================================

    @staticmethod
    def _contains_keyword(
        text: str,
        keyword: str,
    ) -> bool:

        text = str(
            text or ""
        ).lower()

        keyword = str(
            keyword or ""
        ).strip().lower()

        if not text or not keyword:

            return False

        pattern = rf"(?<!\w){re.escape(keyword)}(?!\w)"

        return bool(
            re.search(
                pattern,
                text,
            )
        )

    @classmethod
    def _matching_keywords(
        cls,
        text: str,
        keywords,
    ) -> list:

        return [
            keyword
            for keyword in keywords
            if cls._contains_keyword(
                text,
                keyword,
            )
        ]

    # ======================================================
    # OPPORTUNITY TEXT
    # ======================================================

    @staticmethod
    def _get_opportunity_text(
        opportunity,
    ) -> tuple:

        title = str(
            opportunity.get(
                "title",
                "",
            )
            or ""
        ).strip()

        snippet = str(
            opportunity.get(
                "snippet",
                "",
            )
            or ""
        ).strip()

        description = str(
            opportunity.get(
                "description",
                "",
            )
            or ""
        ).strip()

        url = str(
            opportunity.get(
                "url",
                "",
            )
            or opportunity.get(
                "source_url",
                "",
            )
            or ""
        ).strip()

        combined = " ".join(
            [
                title,
                snippet,
                description,
                url,
            ]
        ).lower()

        return (
            title.lower(),
            snippet.lower(),
            description.lower(),
            url.lower(),
            combined,
        )

    # ======================================================
    # URL / TITLE CANONICALIZATION (for deduplication)
    # ======================================================

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        """
        Normalize a URL for deduplication purposes:
        - lowercase scheme/host
        - drop the fragment
        - strip trailing slash from the path
        - remove tracking query parameters (utm_*, fbclid, etc.)
        - sort remaining query parameters for stable comparison
        """

        if not url:
            return ""

        url = url.strip()

        if not url:
            return ""

        try:
            parts = urlsplit(url)
        except ValueError:
            return url.lower()

        scheme = (parts.scheme or "https").lower()

        netloc = parts.netloc.lower()

        path = parts.path or ""

        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

        query_pairs = parse_qsl(parts.query, keep_blank_values=True)

        filtered_pairs = [
            (key, value)
            for key, value in query_pairs
            if key.lower() not in TRACKING_PARAMS
            and not key.lower().startswith(TRACKING_PARAM_PREFIXES)
        ]

        filtered_pairs.sort(key=lambda pair: pair[0].lower())

        query = urlencode(filtered_pairs)

        canonical = urlunsplit((scheme, netloc, path, query, ""))

        return canonical.lower()

    @staticmethod
    def _canonicalize_title(title: str) -> str:
        """
        Normalize a title for deduplication purposes:
        lowercase, strip punctuation, collapse whitespace.
        """

        if not title:
            return ""

        value = title.lower()

        value = re.sub(r"[^\w\s]", " ", value)

        value = re.sub(r"\s+", " ", value).strip()

        return value

    # ======================================================
    # OPPORTUNITY ANALYSIS
    # ======================================================

    def _analyze_opportunity(
        self,
        opportunity,
    ) -> dict:
        """
        Perform a single pass over an opportunity's combined text and
        gather every keyword-matching signal needed by both
        validation and scoring. This avoids re-scanning the same text
        multiple times for unrelated purposes.
        """

        (
            title,
            snippet,
            description,
            url,
            combined,
        ) = self._get_opportunity_text(opportunity)

        return {
            "portal_blocked": any(
                site in url for site in PORTAL_BLOCKLIST
            ),
            "bad_url": any(
                pattern in url for pattern in BAD_URL_PATTERNS
            ),
            "url_hint": any(
                hint in url for hint in TENDER_URL_HINTS
            ),
            "tender_matches": self._matching_keywords(
                combined, TENDER_KEYWORDS
            ),
            "strong_matches": self._matching_keywords(
                combined, STRONG_RELEVANCE_KEYWORDS
            ),
            "consultancy_matches": self._matching_keywords(
                combined, CONSULTANCY_KEYWORDS
            ),
            "unrelated_matches": self._matching_keywords(
                combined, UNRELATED_SERVICE_KEYWORDS
            ),
        }

    # ======================================================
    # DISCOVERY SCORING / VALIDATION
    # ======================================================

    def _score_opportunity(
        self,
        opportunity,
    ) -> tuple:
        """
        Validate and score an opportunity for discovery-time
        relevance, in a single pass over its text signals.

        Returns:
            (is_valid: bool, score: int)
        """

        analysis = self._analyze_opportunity(opportunity)

        # --------------------------------------------------
        # BLOCK KNOWN AGGREGATOR PORTALS / LISTING PAGES
        # --------------------------------------------------

        if analysis["portal_blocked"] or analysis["bad_url"]:
            return False, 0

        # --------------------------------------------------
        # REQUIRE A TENDER / OPPORTUNITY SIGNAL
        # --------------------------------------------------

        if not analysis["tender_matches"] and not analysis["url_hint"]:
            return False, 0

        # --------------------------------------------------
        # MIXED-CONTENT / UNRELATED SERVICE HANDLING
        #
        # A page containing an unrelated-service term is only kept
        # when it also has strong structural relevance, or a solid
        # (2+) consultancy signal combined with a tender/url signal.
        # --------------------------------------------------

        if analysis["unrelated_matches"] and not analysis["strong_matches"]:

            has_minimum_consultancy_signal = (
                len(analysis["consultancy_matches"]) >= 2
                and (analysis["tender_matches"] or analysis["url_hint"])
            )

            if not has_minimum_consultancy_signal:
                return False, 0

        # --------------------------------------------------
        # REQUIRE SOME LIVEHOOAH RELEVANCE
        # --------------------------------------------------

        is_valid = bool(analysis["strong_matches"]) or (
            bool(analysis["consultancy_matches"])
            and (analysis["tender_matches"] or analysis["url_hint"])
        )

        if not is_valid:
            return False, 0

        # --------------------------------------------------
        # SCORE
        # --------------------------------------------------

        score = 0

        score += min(len(analysis["strong_matches"]) * 30, 120)
        score += min(len(analysis["consultancy_matches"]) * 15, 60)
        score += min(len(analysis["tender_matches"]) * 10, 40)

        if analysis["url_hint"]:
            score += 10

        score -= min(len(analysis["unrelated_matches"]) * 25, 75)

        score = max(score, 0)

        return True, score

    # ======================================================
    # SEARCH
    # ======================================================

    def search(
        self,
        query: str,
    ):

        opportunities = []

        # ==================================================
        # SERP SEARCH
        # ==================================================

        try:

            results = self.serp_search.search(
                query
            )

            if results:

                for result in results:
                    result.setdefault("discovery_source", "serp")

                opportunities.extend(
                    results
                )

        except Exception:

            logger.exception(
                "SERP search failed | query=%s",
                query,
            )

        # ==================================================
        # SCRAPER SEARCH
        # ==================================================

        try:

            results = self.scraper_search.search(
                query
            )

            if results:

                for result in results:
                    result.setdefault("discovery_source", "scraper")

                opportunities.extend(
                    results
                )

        except Exception:

            logger.exception(
                "Scraper search failed | query=%s",
                query,
            )

        # ==================================================
        # DEDUPLICATION (canonical URL + normalized title)
        # ==================================================

        seen_urls = set()
        seen_titles = set()

        deduped_opportunities = []

        for opportunity in opportunities:

            raw_url = (
                opportunity.get("url")
                or opportunity.get("source_url")
                or ""
            ).strip()

            if not raw_url:
                continue

            canonical_url = self._canonicalize_url(raw_url)

            if not canonical_url or canonical_url in seen_urls:
                continue

            canonical_title = self._canonicalize_title(
                opportunity.get("title", "")
            )

            if canonical_title and canonical_title in seen_titles:
                continue

            seen_urls.add(canonical_url)

            if canonical_title:
                seen_titles.add(canonical_title)

            deduped_opportunities.append(opportunity)

        opportunities = deduped_opportunities

        # ==================================================
        # PRE-EXTRACTION TENDER FILTER + SCORING
        # ==================================================

        scored_opportunities = []

        for opportunity in opportunities:

            is_valid, score = self._score_opportunity(opportunity)

            if not is_valid or score < MIN_DISCOVERY_SCORE:
                continue

            opportunity["discovery_score"] = score

            scored_opportunities.append(opportunity)

        scored_opportunities.sort(
            key=lambda opp: opp.get("discovery_score", 0),
            reverse=True,
        )

        filtered_opportunities = scored_opportunities

        logger.info(
            "Filtered %d -> %d relevant tender candidates",
            len(opportunities),
            len(filtered_opportunities),
        )

        # ==================================================
        # TENDER INTELLIGENCE
        #
        # This remains in the existing architecture for now.
        # It is intentionally not redesigned in this step.
        # ==================================================

        analyzed_opportunities = []

        for opportunity in filtered_opportunities:

            try:

                intelligence = (
                    self.intelligence.analyze(
                        opportunity
                    )
                )

                enriched_opportunity = {
                    **opportunity,
                    "intelligence": intelligence,
                }

                analyzed_opportunities.append(
                    enriched_opportunity
                )

            except Exception:

                logger.exception(
                    "Intelligence analysis failed | title=%s",
                    opportunity.get("title", "Unknown"),
                )

                analyzed_opportunities.append(
                    opportunity
                )

        return analyzed_opportunities