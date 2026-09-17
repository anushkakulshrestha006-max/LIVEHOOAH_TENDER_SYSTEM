from core.services.scraper_search import ScraperSearch

s = ScraperSearch()

q = "structural consultant empanelment"

html = s._fetch_page(
    "https://iitd.ac.in/tenders-archive.php"
)

print("=" * 100)
print("IITD ARCHIVE CONTEXT DIAGNOSTIC")
print("=" * 100)

from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")

targets = [
    "Empanelment of Architectural consultants",
    "Rehabilitation and Retrofitting of RCC Slabs",
    "Special Structural Repair work in B-Type",
    "Structural Glazing facade work",
    "Anti- Bird Spikes",
    "Retrofitting) VF Drive",
]

for target in targets:

    print("\n" + "=" * 100)
    print("TARGET:", target)
    print("=" * 100)

    found = False

    for link in soup.find_all("a", href=True):

        text = link.get_text(
            " ",
            strip=True,
        )

        if target.lower() not in text.lower():
            continue

        found = True

        absolute = s._normalize_url(
            __import__("urllib.parse", fromlist=["urljoin"]).urljoin(
                "https://iitd.ac.in/tenders-archive.php",
                link.get("href"),
            )
        )

        context = s._extract_link_context(
            link,
            "",
        )

        combined = " ".join(
            value
            for value in (
                text,
                absolute,
                context,
            )
            if value
        ).lower()

        print("ANCHOR TEXT:")
        print(text)

        print("\nURL:")
        print(absolute)

        print("\nCONTEXT:")
        print(context)

        print("\n--- SIGNALS ---")

        print(
            "QUERY SCORE:",
            s._query_relevance_score(
                combined,
                q,
            ),
        )

        print(
            "STRUCTURAL SCORE:",
            s._structural_relevance_score(
                combined,
            ),
        )

        print(
            "OPPORTUNITY SCORE:",
            s._opportunity_evidence_score(
                combined,
            ),
        )

        print(
            "STRONG STRUCTURAL COUNT:",
            s._strong_structural_signal_count(
                combined,
            ),
        )

        print(
            "STRONG STRUCTURAL:",
            s._has_strong_structural_signal(
                combined,
            ),
        )

        print(
            "STRONG PROCUREMENT:",
            s._has_strong_procurement_signal(
                combined,
            ),
        )

        print(
            "DOCUMENT:",
            s._is_document_url(
                absolute,
            ),
        )

        print(
            "CANDIDATE SCORE:",
            s._candidate_score(
                text,
                absolute,
                q,
                context,
            ),
        )

        print(
            "LOOKS LIKE TENDER:",
            s._looks_like_tender_link(
                text,
                absolute,
                q,
                context,
            ),
        )

        print()

    if not found:
        print("TARGET NOT FOUND")

print("\n" + "=" * 100)
print("DONE")
print("=" * 100)
