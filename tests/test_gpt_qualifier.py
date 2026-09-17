from pprint import pprint

from core.services.gpt_qualifier import GPTQualifier


qualifier = GPTQualifier()

result = qualifier.qualify(
    {
        "title": "Empanelment of Structural Consultants",

        "intelligence": {
            "confidence": 1.0,
            "service_category":
                "structural consultancy"
        }
    }
)

pprint(result)