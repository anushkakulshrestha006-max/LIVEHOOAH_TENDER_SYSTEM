import pytest

from core.services.tender_intelligence import TenderIntelligence


@pytest.fixture
def agent():
    return TenderIntelligence()


def test_structural_tender_is_relevant(agent):
    result = agent.analyze({
        "title": "Empanelment of Structural Consultants",
        "description": "Structural engineering consultancy services",
        "source_url": "https://example.com/tender/123",
    })

    assert result["is_relevant"] is True
    assert result["service_category"] == "structural consultancy"
    assert result["confidence"] > 0


def test_stronger_structural_signals_outweigh_unrelated_signal(agent):
    result = agent.analyze({
        "title": "Tender for Structural Engineering Consultancy",
        "description": (
            "Structural engineering consultancy for building design "
            "and structural analysis. The project also includes "
            "minor road coordination."
        ),
        "source_url": "https://example.com/tender/456",
    })

    assert result["is_relevant"] is True
    assert result["confidence"] > 0
