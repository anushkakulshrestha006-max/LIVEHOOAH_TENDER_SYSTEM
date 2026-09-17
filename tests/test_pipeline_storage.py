from sheets.sheets_transformer import transform_opportunity
from utils.validators import validate_opportunity


def test_pipeline_transform_and_validate():

    opportunity = {
        "title": "Delhi Road Construction Tender",
        "location": "Delhi",
        "source": "GeM",
        "source_url": "https://gem.gov.in/test",
        "experience_score": 0.91
    }

    transformed = transform_opportunity(
        opportunity
    )

    assert transformed["priority"] == "HIGH"

    assert validate_opportunity(
        transformed
    ) is True