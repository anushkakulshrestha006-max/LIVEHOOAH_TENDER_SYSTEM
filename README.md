# LIVEHOOAH Tender Intelligence System

Automated tender discovery, extraction, qualification, deduplication, and Google Sheets storage pipeline for Livehooah Technology Pvt Ltd.

The current handoff focuses on backend correctness, reproducible operation, and data quality. Dashboard and analytics work is outside the current backend handoff scope.

## Current Status

The backend pipeline is covered by a deterministic pytest suite.

Current validated baseline:

- Python version: 3.9.6
- Deterministic tests: 163 passing
- Known dependency/runtime warnings: 7
- Configured base discovery queries: 50
- Deterministic tests do not require live SERP or Google Sheets access

## Runtime Architecture

The reachable production path is:

main.py
-> run_daily_tender_job()
-> SearchBudget
-> run_livehooah_pipeline()
-> LIVEHOOAH_QUERIES
-> run_pipeline()
-> Tender discovery
-> SearchRouter
-> SERP API and ScraperSearch
-> TenderExtractionEngine
-> PDF or HTML extraction
-> Tender parsing and intelligence
-> Livehooah relevance scoring
-> Qualification
-> Deduplication
-> Sheets transformation
-> Google Sheets

The production entry point is main.py.

The repository currently does not contain its own production scheduler. Recurring execution must be provided externally by the deployment environment.

## Runtime Configuration

The reachable runtime uses these environment variable names:

- SERPAPI_KEY
- SERP_DAILY_REQUEST_LIMIT

SERP_DAILY_REQUEST_LIMIT controls paid SERP attempts across one complete daily run.

A value of 0 disables paid SERP access.

If SERP_DAILY_REQUEST_LIMIT is missing, the daily job defaults it to 0.

Malformed or negative values fail fast.

One SearchBudget is shared across all discovery queries and retries during the run.

A SERP provider failure consumes that attempt and disables further SERP use for the shared run. Scraper-based discovery can continue.

## Google Sheets Configuration

Google service-account credentials are expected in the project-relative config/service_account.json file.

The credential file is intentionally ignored by Git and must never be committed.

The configured workbook is LIVEHOOAH Opportunity Intelligence Hub.

Expected worksheets:

- Opportunities
- Contacts
- Keywords
- Activity_Log
- Existing_Client_Watchlist
- HIGH_PRIORITY
- MEDIUM_PRIORITY
- LOW_PRIORITY

## Logging

Runtime logs are stored in the project-relative logs directory.

The directory is created automatically when logging initializes and is intentionally ignored by Git.

## Scoring and Qualification

The minimum Livehooah relevance score required for qualification is 0.60.

Canonical priority boundaries:

- HIGH: score greater than or equal to 0.70
- MEDIUM: score greater than or equal to 0.50 and below 0.70
- LOW: score below 0.50

Relevance scoring and qualification are separate stages.

Qualification checks include:

- valid organization and tender data;
- title length and quality;
- source URL availability;
- tender expiry;
- rejection of reference or application documents;
- presence of an active opportunity signal;
- minimum Livehooah relevance score.

## Deduplication

Core deduplication is intentionally conservative.

The rules are:

1. Exact source URL match.
2. Title, organization, and deadline fingerprint only when all required values are present.
3. Fuzzy title matching at the configured threshold only when organization and deadline are present and equal.

Incomplete metadata is preserved instead of being aggressively classified as duplicate.

Google Sheets duplicate detection requires both normalized title and source link to match.

## Google Sheets Data Contract

Opportunity IDs use the OPP-###### format.

Contact IDs use the CNT-###### format.

Default opportunity status is NEW.

Default contact status is NOT_CONTACTED.

The locked Opportunities sheet columns are:

1. Opportunity_ID
2. Type
3. Title
4. Organization
5. Service_Category
6. Location
7. Source
8. Source_Link
9. Deadline
10. Contact_Status
11. Opportunity_Status
12. Priority
13. Score
14. Qualified
15. Qualification_Score
16. Recommended_Action
17. Qualification_Reasoning
18. Summary
19. Assigned_To
20. Last_Updated
21. Date_Added

## Failure Behavior

Expected operational failures are isolated where practical.

Discovery failures are retried by the per-query pipeline.

Individual extraction failures are logged and counted without stopping processing of other discovered opportunities.

Individual Google Sheets write failures are logged and counted.

Unexpected failures outside these protected operational boundaries may propagate to the caller. They should not automatically be hidden as successful execution.

## Automated Testing

The deterministic pytest suite currently has a validated baseline of 163 passing tests and 7 known warnings.

The warnings currently include Python 3.9 end-of-life warnings from Google authentication dependencies and SWIG-related deprecation warnings.

The deterministic suite is designed not to consume live SERP quota or perform live Google Sheets writes.

The established development workflow is:

1. Inspect the reachable implementation, callers, and existing tests.
2. Establish the intended contract.
3. Reproduce a concrete defect.
4. Add the smallest deterministic failing regression test.
5. Confirm the expected failure.
6. Make the minimum production change.
7. Run the focused test.
8. Run affected regression tests.
9. Run the complete deterministic suite.
10. Inspect Git diffs before staging.
11. Stage only the logical change.
12. Inspect the cached diff.
13. Create one logical commit.

## Manual Integration Checks

Network-dependent, quota-consuming, credential-dependent, or write-capable diagnostic scripts are isolated under scripts/manual_checks.

Read scripts/manual_checks/README.md before running them.

Depending on the script, a manual check may:

- make real network requests;
- consume SERP or API quota;
- require local credentials;
- access Google Sheets;
- write records to Google Sheets;
- require WSL, Hermes, or another external runtime.

These scripts are intentionally excluded from normal automated pytest collection.

## Installation and Runtime Notes

The project is currently validated with Python 3.9.6.

For a fresh installation, create a Python virtual environment and install the dependencies declared in requirements.txt.

For an existing working installation, do not recreate the virtual environment unnecessarily.

Python 3.9 is end-of-life. Some current Google authentication dependencies therefore emit compatibility warnings. A future Python upgrade should be performed as a controlled maintenance change and followed by the complete deterministic regression suite.

The currently validated dependency versions are recorded in requirements.txt.

## Running the Production Entry Point

The production entry point is main.py.

Run it only when a real pipeline execution is intended.

A normal production execution may:

- access external websites;
- use paid SERP quota when SERP_DAILY_REQUEST_LIMIT is greater than zero;
- fetch tender documents;
- connect to Google Sheets;
- write qualified opportunities to Google Sheets.

Do not use a production execution as a substitute for automated tests.

## Deployment

The repository does not currently contain a production scheduler.

Recurring execution must be configured externally by the deployment owner.

Before production execution, verify:

1. The intended Python virtual environment is active.
2. Dependencies from requirements.txt are installed.
3. SERP_DAILY_REQUEST_LIMIT has the intended value.
4. SERPAPI_KEY is configured when paid SERP access is enabled.
5. config/service_account.json exists locally.
6. The Google service account can access the configured workbook.
7. The deterministic pytest suite passes.
8. The runtime account can write to the project logs directory.
9. An external scheduler is configured if recurring execution is required.

## Credential and Secret Handling

Never commit:

- .env
- config/service_account.json
- service.json
- API keys
- Google service-account credentials

The known local credential files and environment file are covered by .gitignore.

If an API key or credential is accidentally exposed, revoke or rotate it. Removing the value from a local file alone is not sufficient after exposure.

## Known Limitations

Python 3.9.6 is the currently validated interpreter but is end-of-life.

The repository does not currently provide its own production scheduler.

The current backend handoff does not include a completed dashboard or analytics layer.

Manual integration scripts may depend on external services and should not be treated as deterministic regression tests.

Live external systems can fail independently of the deterministic application tests.

## Handoff Priorities

The current backend handoff prioritizes:

- reliable tender discovery;
- controlled SERP spending;
- structured PDF and HTML extraction;
- deterministic tender parsing and intelligence;
- Livehooah-specific relevance scoring;
- active-opportunity qualification;
- conservative deduplication;
- stable Google Sheets transformation and storage;
- deterministic regression testing;
- reproducible runtime paths and configuration;
- safe credential handling.

Stable components should not be redesigned without a demonstrated defect and an appropriate regression test.

Dashboard and analytics development, broader deployment automation, and a controlled Python-version upgrade can be handled as later work.
