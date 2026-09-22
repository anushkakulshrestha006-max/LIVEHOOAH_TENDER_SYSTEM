from utils.id_generator import generate_id


def test_generate_opportunity_id():
    assert generate_id("OPP", 1) == "OPP-000001"


def test_generate_contact_id():
    assert generate_id("CNT", 25) == "CNT-000025"
