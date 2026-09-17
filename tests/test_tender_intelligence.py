from core.services.tender_intelligence import TenderIntelligence

agent = TenderIntelligence()

result = agent.analyze({
    "title": "Empanelment of Structural Consultants",
    "description": "Structural engineering consultancy services",
    "source_url": "https://example.com"
})

print(result)