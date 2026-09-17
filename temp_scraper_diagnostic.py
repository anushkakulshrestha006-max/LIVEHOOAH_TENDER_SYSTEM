from core.services.scraper_search import ScraperSearch

s = ScraperSearch()
q = "structural consultant empanelment"

selected = s._select_sources(q)

print("SELECTED SOURCES:", len(selected))
print("=" * 80)

total = 0
seen = set()

for source in selected:
    source_url = s._normalize_url(source.get("url", ""))

    print("\nSOURCE:", source_url)

    if not source_url:
        print("  SKIPPED: empty URL")
        continue

    source_opportunities, pages = s._crawl_source(
        source_url,
        q,
    )

    print("  PAGES:", pages)
    print("  CANDIDATES:", len(source_opportunities))

    for opportunity in source_opportunities:
        url = opportunity.get("source_url")

        if not url:
            print("    SKIP: empty source_url")
            continue

        if url in seen:
            print("    DUPLICATE:", url)
            continue

        seen.add(url)
        total += 1

        if source_url == "https://iitd.ac.in":
            print(
                "    IITD:",
                opportunity.get("title"),
                "|",
                url,
            )

print("\n" + "=" * 80)
print("UNIQUE CANDIDATES:", total)
