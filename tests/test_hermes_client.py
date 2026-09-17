from agents.hermes_client import HermesClient
from agents.tender_discovery_agent import run_tender_discovery


def test_hermes_discovery():
    hermes = HermesClient()

    prompt = "Find a road construction tender in Uttar Pradesh"

    output = hermes.run(prompt)

    assert output is not None
    assert len(output) > 0

    print("Discovery Output:", output)


def test_hermes_json_mode():
    hermes = HermesClient()

    output = hermes.run_json('{"task":"return status ok"}')

    assert isinstance(output, dict)
    assert output.get("task") == "return status ok"

    print("JSON Output:", output)
def test_basic_run():
    result = run_tender_discovery("Find road tenders in Delhi NCR")

    assert "opportunities" in result
    assert "meta" in result