from core.services.opportunity_pipeline import run_pipeline
from agents.tender_discovery_agent import LIVEHOOAH_QUERIES

all_results = []

for query in LIVEHOOAH_QUERIES:

    print(f"\nRunning: {query}")

    result = run_pipeline(query)

    all_results.append(result)

print(all_results)