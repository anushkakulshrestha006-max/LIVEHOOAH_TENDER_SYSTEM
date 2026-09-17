from pprint import pprint
from serpapi import GoogleSearch
from dotenv import load_dotenv
import os

load_dotenv()

params = {
    "engine": "google",
    "q": "structural consultant tender site:gov.in",
    "gl": "in",
    "hl": "en",
    "num": 10,
    "api_key": os.getenv("SERPAPI_KEY"),
}

search = GoogleSearch(params)

results = search.get_dict()

print("\nORGANIC RESULTS COUNT:")
print(len(results.get("organic_results", [])))

print("\nFIRST 3 RESULTS:\n")

for result in results.get("organic_results", [])[:3]:
    pprint(result)
    print("\n" + "=" * 80 + "\n")