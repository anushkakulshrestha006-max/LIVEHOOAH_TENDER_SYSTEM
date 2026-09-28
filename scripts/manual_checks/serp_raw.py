from core.services.serp_search import SerpSearch
from pprint import pprint

search = SerpSearch()

results = search.search(
    "structural consultant tender site:gov.in"
)

print("\nFIRST RESULT:\n")
pprint(results[0] if results else {})