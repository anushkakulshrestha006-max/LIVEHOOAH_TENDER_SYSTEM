import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from serpapi import GoogleSearch

# Load .env
load_dotenv()

# ==========================================================
# LOW QUALITY TITLE FILTERS
# ==========================================================

BAD_TITLE_PATTERNS = [
    "latest tenders",
    "tenders in india",
    "search tenders",
    "keyword tenders",
    "government tenders",
    "all tenders",
    "tender listings",
    "latest active tenders",
    "online tenders",
    "directory",
    "top tenders",
    "eprocurement system",
    "award of contract",
    "award notice",
    "contract awarded",
    "corrigendum",
    "corrigenda",
    "results",
    "result",
    "archive",
    "archived",
    "cancelled",
    "cancellation",
    "application form",
    "registration form",
    "vendor registration",
]

# ==========================================================
# AGGREGATOR / LOW VALUE DOMAINS
# ==========================================================

BAD_DOMAINS = [
    "bidassist.com",
    "tendersontime.com",
    "tender247.com",
    "tenderdetail.com",
    "tendersinfo.com",
    "tendernews.com",
    "tenderbazaar.com",
    "tendersniper.com",
    "nationaltenders.com",
    "firsttender.com",
    "globaltenders.com",
    "maharashtratenders.com",
    "delhitenders.com",
    "justdial.com",
    "indiamart.com",
    "sulekha.com",
    "scribd.com",
]

# ==========================================================
# OFFICIAL SOURCES
# ==========================================================

OFFICIAL_DOMAINS = [
    "gov.in",
    "nic.in",
    "etenders.gov.in",
    "eprocure.gov.in",
    "gem.gov.in",
    "cppp.gov.in",
]

# ==========================================================
# POSITIVE SIGNALS
# ==========================================================

POSITIVE_KEYWORDS = [
    "structural",
    "structural consultant",
    "structural consultancy",
    "structural engineering",
    "proof checking",
    "peer review",
    "structural audit",
    "rehabilitation",
    "retrofit",
    "consultancy",
    "consultant",
    "rfp",
    "eoi",
    "expression of interest",
    "empanelment",
    "request for proposal",
    "tender",
]

# ==========================================================
# NEGATIVE SIGNALS
# ==========================================================

NEGATIVE_KEYWORDS = [
    "housekeeping",
    "landscaping",
    "tree cutting",
    "demolition",
    "canteen",
    "cafeteria",
    "restaurant",
    "electrical maintenance",
    "annual maintenance",
    "amc",
    "road",
    "roads",
    "bridge",
    "bridges",
    "highway",
    "railway",
    "airport",
    "drain",
    "drainage",
    "water supply",
    "pipeline",
]

# ==========================================================
# GOOD URL HINTS
# ==========================================================

GOOD_URL_HINTS = [
    "tender",
    "rfp",
    "eoi",
    "empanelment",
    "consultancy",
    "procurement",
    "bid",
]

# ==========================================================
# BAD URL HINTS
# ==========================================================

BAD_URL_HINTS = [
    "/archive",
    "/award",
    "/result",
    "/results",
    "/blog",
    "/news",
    "/category",
    "/categories",
    "/tag",
    "/tags",
    "/search",
]

# ==========================================================
# FILTER HELPERS
# ==========================================================

def should_skip_result(title: str, url: str) -> bool:
    title = (title or "").lower()
    url = (url or "").lower()

    for pattern in BAD_TITLE_PATTERNS:
        if pattern in title:
            return True

    for domain in BAD_DOMAINS:
        if domain in url:
            return True

    for hint in BAD_URL_HINTS:
        if hint in url:
            return True

    return False


def compute_discovery_score(title: str, snippet: str, url: str):
    title = (title or "").lower()
    snippet = (snippet or "").lower()
    url = (url or "").lower()

    combined = f"{title} {snippet}"

    score = 0
    reasons = []

    # ------------------------------------------------------
    # Official source
    # ------------------------------------------------------
    if any(domain in url for domain in OFFICIAL_DOMAINS):
        score += 5
        reasons.append("official_source")

    # ------------------------------------------------------
    # URL hints
    # ------------------------------------------------------
    for hint in GOOD_URL_HINTS:
        if hint in url:
            score += 2

    # ------------------------------------------------------
    # Positive relevance
    # ------------------------------------------------------
    for keyword in POSITIVE_KEYWORDS:
        if keyword in combined:
            score += 2

    # ------------------------------------------------------
    # Negative relevance
    # ------------------------------------------------------
    for keyword in NEGATIVE_KEYWORDS:
        if keyword in combined:
            score -= 4

    return score, reasons


# ==========================================================
# SERP SEARCH CLASS
# ==========================================================

class SerpSearch:

    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")

        print("SERP KEY FOUND:", bool(self.api_key))

        if not self.api_key:
            raise ValueError(
                "SERPAPI_KEY not found in environment"
            )

    def search(self, query: str):
        print(f"🔎 SERP Search: {query}")

        params = {
            "engine": "google",
            "q": query,
            "gl": "in",
            "hl": "en",
            "num": 20,
            "api_key": self.api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        opportunities = []

        organic_results = results.get("organic_results", [])

        print(f"SERP returned {len(organic_results)} raw results")

        for item in organic_results:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("link", "")

            # --------------------------------------------------
            # Hard filtering
            # --------------------------------------------------
            if should_skip_result(title, url):
                print(f"⏭️ Skipping low-quality result: {title}")
                continue

            # --------------------------------------------------
            # Discovery scoring
            # --------------------------------------------------
            discovery_score, reasons = compute_discovery_score(
                title,
                snippet,
                url,
            )

            # Reject obviously poor candidates
            if discovery_score < 0:
                print(f"⛔ Rejected ({discovery_score}) : {title}")
                continue

            opportunity = {
                "title": title,
                "description": snippet,
                "source_url": url,
                "organization": "",
                "location": "",
                "discovery_score": discovery_score,
                "discovery_reasoning": ", ".join(reasons),
            }

            opportunities.append(opportunity)

        # ------------------------------------------------------
        # Highest quality first
        # ------------------------------------------------------
        opportunities.sort(
            key=lambda x: (
                x.get("discovery_score", 0),
                len(x.get("title", "")),
            ),
            reverse=True,
        )

        print()
        print("=" * 70)
        print("SERP DISCOVERY SUMMARY")
        print("=" * 70)

        for opp in opportunities:
            print(f"[{opp['discovery_score']:>2}] {opp['title']}")

        print("=" * 70)
        print(f"✅ Returning {len(opportunities)} ranked opportunities")

        return opportunities