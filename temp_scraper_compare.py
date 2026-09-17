from core.services.scraper_search import ScraperSearch

s = ScraperSearch()
q = "structural consultant empanelment"

print("=" * 80)
print("DIRECT _CRAWL_SOURCE")
print("=" * 80)

direct, direct_pages = s._crawl_source(
    "https://iitd.ac.in",
    q,
)

print("DIRECT PAGES:", direct_pages)
print("DIRECT COUNT:", len(direct))
print("DIRECT FIRST:", direct[0] if direct else None)

print()
print("=" * 80)
print("FULL SEARCH")
print("=" * 80)

result = s.search(q)

print("SEARCH COUNT:", len(result))

iitd = [
    x for x in result
    if "iitd.ac.in" in x.get("source_url", "")
]

print("SEARCH IITD COUNT:", len(iitd))

for i, x in enumerate(iitd[:30]):
    print(
        i + 1,
        "|",
        x.get("title"),
        "|",
        x.get("source_url"),
    )

print()
print("=" * 80)
print("DONE")
print("=" * 80)
