from pprint import pprint

from core.services.opportunity_pipeline import run_pipeline

result = run_pipeline(
    "structural consultant empanelment"
)

pprint(result)