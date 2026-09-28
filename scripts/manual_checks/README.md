# Manual Integration Checks

The scripts in this directory are historical/manual integration diagnostics.

They are intentionally kept outside `tests/` because they are NOT safe for
automatic pytest execution or collection.

Depending on the script, running one may:

- make real network requests;
- consume SERP/API quota;
- require local credentials or environment variables;
- connect to Google Sheets;
- write records to Google Sheets;
- require WSL/Hermes or another external runtime;
- depend on external services that may be unavailable.

Run these scripts only when explicitly performing the corresponding manual
integration check.

The automated deterministic test suite lives under `tests/`.

Do not move these scripts back under `tests/` unless they are first converted
into isolated pytest tests with all external boundaries mocked or faked.
