import json
import re


def clean_hermes_output(text: str) -> str:
    """
    Removes markdown wrappers and junk from Hermes output
    """

    if not text:
        return ""

    text = text.strip()

    # Remove ```json and ```
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    return text.strip()


def parse_strict_json(text: str) -> dict:

    cleaned = clean_hermes_output(text)

    # Hard extraction: find JSON anywhere in output
    match = re.search(r"\{[\s\S]*\}", cleaned)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    # Fallback safe return (meta injected by HermesClient.run, not here)
    return {
        "opportunities": [],
        "raw_output": cleaned,
        "status": "unstructured"
    }