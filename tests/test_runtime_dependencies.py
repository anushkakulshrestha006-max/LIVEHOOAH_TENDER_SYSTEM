from pathlib import Path


def _declared_packages():
    requirements_path = (
        Path(__file__).resolve().parents[1]
        / "requirements.txt"
    )

    text = requirements_path.read_text(
        encoding="utf-8"
    )

    return {
        line.split("==", 1)[0].strip().lower()
        for line in text.splitlines()
        if line.strip()
        and not line.lstrip().startswith("#")
    }


def test_reachable_serp_dependencies_are_declared():
    declared = _declared_packages()

    assert "python-dotenv" in declared
    assert "google-search-results" in declared
