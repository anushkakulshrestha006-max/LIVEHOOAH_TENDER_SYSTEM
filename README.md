<![CDATA[# LIVEHOOAH Tender Intelligence System

> **Automated tender discovery, extraction, scoring, and qualification pipeline for LiveHooah — a structural engineering consultancy firm.**

The system autonomously discovers government and institutional tenders relevant to structural engineering consultancy (structural audit, proof checking, retrofitting, high-rise design, etc.), extracts structured data from tender documents, scores them for business relevance, qualifies them against LiveHooah's capabilities, and stores qualified opportunities in a Google Sheets–based Opportunity Intelligence Hub.

---

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Pipeline Stages](#pipeline-stages)
  - [Stage 1 — Daily Job Trigger](#stage-1--daily-job-trigger)
  - [Stage 2 — Query Expansion & Discovery](#stage-2--query-expansion--discovery)
  - [Stage 3 — Search Execution](#stage-3--search-execution)
  - [Stage 4 — Discovery-Time Filtering & Scoring](#stage-4--discovery-time-filtering--scoring)
  - [Stage 5 — Tender Intelligence Analysis](#stage-5--tender-intelligence-analysis)
  - [Stage 6 — Document Extraction](#stage-6--document-extraction)
  - [Stage 7 — Content Deduplication](#stage-7--content-deduplication)
  - [Stage 8 — LiveHooah Relevance Scoring](#stage-8--livehooah-relevance-scoring)
  - [Stage 9 — Opportunity Qualification](#stage-9--opportunity-qualification)
  - [Stage 10 — Data Transformation & Storage](#stage-10--data-transformation--storage)
- [Project Structure](#project-structure)
- [Module Reference](#module-reference)
  - [Core Services](#core-services)
  - [Scoring Engine](#scoring-engine)
  - [Agents](#agents)
  - [LLM Layer](#llm-layer)
  - [Google Sheets Integration](#google-sheets-integration)
  - [Configuration](#configuration)
  - [Utilities](#utilities)
  - [Infrastructure](#infrastructure)
  - [Dashboard](#dashboard)
- [Data Flow Diagram](#data-flow-diagram)
- [Google Sheets Schema](#google-sheets-schema)
- [Configuration Reference](#configuration-reference)
- [Environment Variables](#environment-variables)
- [Installation & Setup](#installation--setup)
- [Running the Pipeline](#running-the-pipeline)
- [Running the Dashboard](#running-the-dashboard)
- [Testing](#testing)
- [Design Principles](#design-principles)
- [Technology Stack](#technology-stack)

---

## System Overview

The LiveHooah Tender Intelligence System is a **fully automated, end-to-end pipeline** that:

1. **Discovers** tender opportunities from 60+ official government procurement portals and Google Search (via SerpAPI)
2. **Extracts** structured tender data from HTML pages and PDF documents
3. **Scores** each opportunity against LiveHooah's structural engineering business profile
4. **Qualifies** opportunities based on validity, freshness, active signals, and relevance thresholds
5. **Stores** qualified opportunities in a centralized Google Sheets hub with automatic priority routing
6. **Visualizes** pipeline health and opportunity analytics via a Streamlit dashboard

The entire system is **deterministic** — all scoring, classification, and qualification decisions are rule-based with no LLM dependency in the critical path.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          main.py (Entry Point)                         │
│                    loads .env → runs daily_tender_job                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   jobs/daily_tender_job.py                              │
│         Configures SearchBudget → runs run_livehooah_pipeline()         │
│                Logs run summary to Activity_Log sheet                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              core/services/opportunity_pipeline.py                      │
│                    run_livehooah_pipeline()                             │
│        Iterates all LIVEHOOAH_QUERIES with scoped budgets              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────────┐
           ▼                   ▼                        ▼
    ┌──────────┐       ┌──────────────┐         ┌─────────────┐
    │ Discovery│       │  Extraction  │         │  Scoring &  │
    │  Stage   │──────▶│    Stage     │────────▶│Qualification│
    └──────────┘       └──────────────┘         └──────┬──────┘
                                                       │
                                                       ▼
                                              ┌────────────────┐
                                              │  Transform &   │
                                              │  Google Sheets  │
                                              └────────────────┘
```

---

## Pipeline Stages

### Stage 1 — Daily Job Trigger

**File:** `main.py` → `jobs/daily_tender_job.py`

The system entry point loads environment variables from `.env` and invokes `run_daily_tender_job()`, which:

1. Reads the `SERP_DAILY_REQUEST_LIMIT` from the environment (default: 12)
2. Creates a `SearchBudget` to cap paid SerpAPI calls across the entire run
3. Calls `run_livehooah_pipeline()` from the opportunity pipeline
4. Logs a run summary (queries, qualified, saved, duplicates, failures) to the `Activity_Log` sheet

The `JobRunner` class in `core/job_runner.py` provides a crash-safe wrapper that catches any unhandled exceptions and returns a structured `safe_fail` response instead of crashing.

---

### Stage 2 — Query Expansion & Discovery

**File:** `agents/tender_discovery_agent.py`

The discovery agent manages **56+ base queries** organized by LiveHooah's business verticals:

| Category | Example Queries |
|---|---|
| Core Structural Consultancy | `structural consultant tender`, `appointment of structural consultant` |
| Structural Audit / Assessment | `structural audit`, `building condition assessment` |
| Retrofitting / Rehabilitation | `retrofitting consultancy`, `structural rehabilitation` |
| Proof Checking / Peer Review | `proof checking consultant`, `structural design review` |
| Warehouse / Industrial | `warehouse structural design`, `PEB structural consultant` |
| Buildings | `high rise structural consultant`, `hospital structural consultant` |
| Government / Urban | `smart city engineering consultancy` |

Each base query is expanded via `expand_query()` into multiple search variants:

```
structural audit
  → structural audit tender 2026
  → structural audit 2026
  → structural audit
  → structural audit tender
  → structural audit RFP
  → structural audit RFP PDF
  → structural audit EOI
  → structural audit EOI PDF
  → structural audit empanelment
  → structural audit consultancy services
  → structural audit government tender
  → structural audit eprocurement
```

If the expanded query does not already contain LiveHooah-relevant keywords (e.g. `structural`, `consultant`, `audit`), the system prepends `"structural engineering consultancy"` as a query prefix.

---

### Stage 3 — Search Execution

**File:** `core/services/search_router.py`

The `SearchRouter` orchestrates **two complementary discovery backends**:

#### 3a. SerpAPI Search (`core/services/serp_search.py`)

- Uses the SerpAPI Google Search API (`engine: google`, region: India)
- Returns up to 20 organic results per query
- Applies hard filters: blocks aggregator domains (BidAssist, TenderDetail, etc.), low-quality title patterns, and bad URL patterns
- Computes a discovery score based on: official source bonus, URL hints, positive/negative keyword signals
- Budget-controlled via `SearchBudget` — each query consumes 1 SERP credit

#### 3b. Direct Scraper Search (`core/services/scraper_search.py`)

- Crawls **60+ official government procurement portals** directly (CPWD, NBCC, IIT campuses, municipal corporations, development authorities, etc.)
- Configured in `config/official_sources.py` with per-source metadata: keywords, category, crawl depth, tender paths, priority
- Implements a bounded BFS crawler: max 12 pages per source, max depth 2, 20-second timeout per source
- Discovers navigation/procurement pages intelligently, then extracts tender-relevant links
- Applies comprehensive filtering: rejects career pages, login pages, investor pages, corporate pages, JavaScript-only links

Both backends merge their results, which are then **deduplicated** by canonical URL and normalized title before downstream processing.

---

### Stage 4 — Discovery-Time Filtering & Scoring

**File:** `core/services/search_router.py` → `_score_opportunity()`

Before expensive extraction, each candidate goes through a multi-signal validation and scoring pass:

| Signal | Action |
|---|---|
| **Portal Blocklist** | Reject known aggregator domains |
| **Bad URL Patterns** | Reject category pages, search pages, login pages |
| **Tender Keywords** | Must contain at least one tender/procurement signal |
| **Strong Relevance** | Check for 45+ structural engineering keywords |
| **Consultancy Signals** | Check for consultancy-related terms |
| **Unrelated Services** | Penalize/reject landscaping, housekeeping, HVAC, catering, etc. |

The scoring formula:

```
score  = strong_matches × 30 (max 120)
       + consultancy_matches × 15 (max 60)
       + tender_matches × 10 (max 40)
       + url_hint × 10
       - unrelated_matches × 25 (max 75)
```

Candidates scoring below `MIN_DISCOVERY_SCORE = 10` are dropped.

---

### Stage 5 — Tender Intelligence Analysis

**File:** `core/services/tender_intelligence.py`

The `TenderIntelligence` class is a deterministic analysis layer that:

- Detects genuine structural engineering relevance
- Classifies the service category (structural audit, proof checking, retrofit consultancy, structural design, etc.)
- Produces a summary and reasoning
- Calculates a confidence score
- Rejects directory/listing pages and non-structural work

The intelligence output (service_category, summary, confidence, why_selected) is attached to each opportunity for downstream use.

---

### Stage 6 — Document Extraction

**File:** `core/services/tender_extraction_engine.py`

The `TenderExtractionEngine` is the **master extraction orchestrator**:

```
URL
  ↓
SourceResolver.resolve()         — resolves to best source (PDF > gov page > original)
  ↓
DocumentFetcher.fetch()          — HTTP fetch with retry, redirect, size limits
  ↓
_is_pdf_document()               — detect document type (PDF vs HTML)
  ↓
PDFExtractor / HTMLExtractor     — extract raw text
  ↓
DocumentCleaner.clean()          — normalize unicode, remove boilerplate
  ↓
_is_valid_document()             — validate: length, error pages, readability
  ↓
TenderParser.parse()             — extract structured fields
  ↓
_is_valid_structured_tender()    — validate parsed result
  ↓
Structured Tender Dict
```

#### Sub-Components:

| Component | File | Responsibility |
|---|---|---|
| **SourceResolver** | `core/services/source_resolver.py` | Resolves URLs to the best available source: PDF > Government page > Portal > Original |
| **DocumentFetcher** | `core/services/document_fetcher.py` | Production-grade HTTP downloader with retry logic, redirect handling, streaming, size limits, MIME detection, login/captcha detection, content hashing |
| **HTMLExtractor** | `core/services/html_extractor.py` | Strips boilerplate (headers, footers, nav, scripts, styles), preserves tables, normalizes whitespace |
| **PDFExtractor** | `core/services/pdf_extractor.py` | Extracts text from PDF bytes using PyMuPDF, removes repeated headers/footers, ignores useless pages |
| **DocumentCleaner** | `core/services/document_cleaner.py` | Conservative text preprocessing: unicode normalization, encoding repair, removes error pages, navigation, cookie notices, JS warnings, page numbers, TOC |
| **TenderParser** | `core/services/tender_parser.py` | 4,755-line deterministic parser that extracts: title, organization, deadline, location, description, tender_type, EMD, document_fee, email, phone, source_url |

The parser uses 90+ regex patterns and contextual heuristics to extract structured fields. It is intentionally **LLM-free** for reliability and consistency.

---

### Stage 7 — Content Deduplication

**File:** `core/services/deduplication.py`

The `DeduplicationService` removes duplicate tenders from multiple sources using a priority chain:

1. **URL matching** — exact URL deduplication
2. **Fingerprint matching** — SHA-256 hash of `title|organization|deadline`
3. **Fuzzy title matching** — `SequenceMatcher` with 92% similarity threshold (only when org + deadline both match)

---

### Stage 8 — LiveHooah Relevance Scoring

**File:** `core/scoring/livehooah_matcher.py`

The canonical business relevance scorer `compute_livehooah_score()` produces a **0.0–1.0 relevance score** with detailed reasoning:

| Scoring Dimension | Weight / Logic |
|---|---|
| **Blocked Keywords** | Hard block on roads, highways, airports, railways, dams, solar, etc. → score = 0.0 |
| **Core Capabilities** | 30+ structural engineering terms with individual weights (0.08–0.25). Capped at 0.55 |
| **Tender Opportunity Signal** | +0.20 if procurement language detected; 0.80× multiplier if absent |
| **LiveHooah Service Signal** | +0.04 per match (max 0.20); 0.90× multiplier if absent |
| **Region Boost** | +0.10 for Delhi/NCR/Noida/Gurgaon; penalties for distant regions |
| **Preferred Organizations** | +0.04–0.06 for CPWD, NBCC, DMRC, IIT, AIIMS, etc. |
| **Official Sources** | +0.03–0.05 for gov.in, gem.gov.in, eprocure.gov.in |
| **Freshness** | +0.15 for fresh, +0.12 for active (≤30d), +0.08 for closing (≤7d), 0.00 for expired |
| **Metadata Completeness** | +0.015 per populated field (max 0.12) |
| **Title Relevance** | Bonus for title-specific structural/consultancy terms |
| **Negative Keywords** | Penalty for roads, highways, housekeeping, etc. |

---

### Stage 9 — Opportunity Qualification

**File:** `core/services/opportunity_pipeline.py` → `qualify_opportunity()`

Qualification is a **separate decision** from scoring. An opportunity must pass ALL checks:

| Check | Condition |
|---|---|
| **Valid Tender** | Has a non-generic title and non-empty organization |
| **Title Length** | ≥ 15 characters |
| **Source URL** | Must be present |
| **Not Expired** | Deadline must be in the future (or missing) |
| **Not Reference Doc** | Must not be an application form, registration form, or certificate |
| **Active Signal** | Must contain procurement language (NIT, RFP, EOI, empanelment, etc.) |
| **Minimum Score** | LiveHooah score ≥ 0.60 |

Only opportunities passing all checks receive `qualification_status = "QUALIFIED"`.

---

### Stage 10 — Data Transformation & Storage

#### Transformation (`sheets/sheets_transformer.py`)

Qualified opportunities are transformed into the Google Sheets schema:

- Computes `priority` from score: HIGH (≥0.70), MEDIUM (≥0.50), LOW (<0.50)
- Calculates `extraction_confidence` based on completeness of organization, deadline, location
- Sets initial statuses: `contact_status = "NOT_CONTACTED"`, `opportunity_status = "NEW"`
- Preserves intelligence metadata, qualification reasoning, and parser version

#### Storage (`sheets/sheets_client.py`)

The `SheetsClient` manages all Google Sheets operations:

- **Authentication:** Google Service Account via `gspread`
- **Duplicate Detection:** Checks existing records by exact title + URL match (with in-memory cache)
- **Priority Routing:** Routes to HIGH_PRIORITY, MEDIUM_PRIORITY, or LOW_PRIORITY sheets
- **Rate Limiting:** Automatic retry on Google API 429 errors (3 retries, exponential backoff)
- **Activity Logging:** Every operation logged to the `Activity_Log` sheet with timestamps

---

## Project Structure

```
livehooah_tender_system/
│
├── main.py                          # Entry point — loads .env, runs daily job
├── requirements.txt                 # Python dependencies
├── pytest.ini                       # Pytest configuration
├── .env                             # Environment variables (API keys, limits)
├── .gitignore                       # Git exclusion rules
│
├── jobs/
│   └── daily_tender_job.py          # Daily pipeline orchestrator
│
├── core/
│   ├── job_runner.py                # Crash-safe job execution wrapper
│   │
│   ├── services/
│   │   ├── opportunity_pipeline.py  # Main pipeline: discovery → extraction → scoring → storage
│   │   ├── search_router.py         # Multi-backend search orchestrator (SERP + Scraper)
│   │   ├── serp_search.py           # SerpAPI Google Search integration
│   │   ├── scraper_search.py        # Direct official website scraper (60+ sources)
│   │   ├── tender_intelligence.py   # Deterministic relevance analysis & categorization
│   │   ├── tender_extraction_engine.py  # Master extraction orchestrator
│   │   ├── source_resolver.py       # URL → best source resolver (PDF priority)
│   │   ├── document_fetcher.py      # Production HTTP downloader with retry/streaming
│   │   ├── html_extractor.py        # HTML → clean text extractor
│   │   ├── pdf_extractor.py         # PDF → text extractor (PyMuPDF)
│   │   ├── document_cleaner.py      # Text preprocessing & normalization
│   │   ├── tender_parser.py         # Deterministic structured field extractor (4,755 lines)
│   │   ├── deduplication.py         # Multi-strategy deduplication service
│   │   ├── search_budget.py         # SERP API budget management
│   │   ├── gpt_qualifier.py         # GPT-based qualification (optional, not in main path)
│   │   └── query_expander.py        # Query expansion utilities
│   │
│   ├── scoring/
│   │   ├── livehooah_matcher.py     # Canonical business relevance scorer
│   │   ├── relevance_classifier.py  # Experience-based relevance classifier
│   │   └── experience_scoring.py    # Legacy scoring wrapper (delegates to livehooah_matcher)
│   │
│   ├── schemas/
│   │   └── opportunity_schema.py    # Opportunity data schema
│   │
│   ├── clients/
│   │   └── hermes_client.py         # Hermes LLM API client
│   │
│   ├── parsers/
│   │   └── hermes_parser.py         # Hermes response parser
│   │
│   └── prompts/
│       └── hermes_tender_prompt.py  # Hermes prompt template
│
├── agents/
│   ├── __init__.py
│   ├── base_agent.py                # Agent base class (placeholder)
│   ├── tender_discovery_agent.py    # Manages discovery queries & search execution
│   ├── qualification_agent.py       # Qualification agent (placeholder)
│   ├── contact_discovery_agent.py   # Contact discovery agent (placeholder)
│   ├── duplicate_agent.py           # Duplicate detection agent (placeholder)
│   ├── lead_discovery_agent.py      # Lead discovery agent (placeholder)
│   ├── opportunity_intelligence_agent.py  # Intelligence agent (placeholder)
│   ├── hermes_client.py             # Hermes client for agent layer
│   └── discovery/
│       ├── discovery_service.py     # Discovery service wrapper
│       ├── query_builder.py         # Query builder utilities
│       └── response_validator.py    # Response validation
│
├── llm/
│   ├── __init__.py
│   ├── router.py                    # LLM Router with fallback chain
│   ├── token_guard.py              # Token budget enforcement
│   ├── llm_bootstrap.py            # LLM initialization
│   ├── providers/
│   │   ├── base.py                  # Provider base class
│   │   ├── gpt_provider.py          # OpenAI GPT provider
│   │   ├── deepseek_provider.py     # DeepSeek provider
│   │   ├── openrouter_provider.py   # OpenRouter provider
│   │   └── laguna_provider.py       # Local Laguna provider
│   └── fallback/
│       └── rule_based.py            # Rule-based fallback (no LLM)
│
├── sheets/
│   ├── __init__.py
│   ├── sheets_client.py             # Google Sheets read/write with caching & retry
│   └── sheets_transformer.py        # Opportunity → Sheets row transformer
│
├── config/
│   ├── __init__.py
│   ├── settings.py                  # Global settings (paths, sheet name)
│   ├── constants.py                 # Sheet names, headers, ID prefixes, status values
│   ├── llm_config.py               # LLM provider configuration & fallback chain
│   ├── livehooah_keywords.py        # Business keyword taxonomy (high priority, engineering, blocked)
│   ├── livehooah_experience.py      # Regional experience data (Tier 1/2/3 regions, clients)
│   ├── official_sources.py          # 60+ official procurement source definitions
│   ├── source_scores.py             # Source quality scores
│   └── service_account.json         # Google Service Account credentials (gitignored)
│
├── utils/
│   ├── logger.py                    # Daily rotating file + console logger
│   ├── duplicate_detector.py        # Title+URL duplicate detection for Sheets
│   ├── validators.py                # Data validation (title, URL, email, opportunity)
│   └── id_generator.py              # Sequential ID generator (OPP-000001, CNT-000001)
│
├── infra/
│   └── error_handler.py             # Safe-fail error wrapper
│
├── dashboard/
│   ├── app.py                       # Streamlit dashboard application
│   └── dashboard_data.py            # Dashboard data loading & metric computation
│
├── prompts/
│   └── v1/                          # Prompt templates (placeholder)
│       ├── tender_discovery.md
│       ├── qualification.md
│       ├── contact_discovery.md
│       ├── duplicate.md
│       ├── lead_discovery.md
│       └── opportunity_intelligence.md
│
├── tests/                           # 38 test files with comprehensive coverage
│   ├── test_livehooah_matcher.py
│   ├── test_tender_extraction_engine.py
│   ├── test_tender_parser.py
│   ├── test_pipeline_extraction_handoff.py
│   ├── test_search_router.py
│   ├── test_scraper_search.py
│   ├── test_document_fetcher.py
│   ├── test_html_extractor.py
│   ├── test_dashboard_data.py
│   ├── test_sheets_client_cache.py
│   ├── test_source_resolver.py
│   ├── ... (38 test files total)
│   └── helpers/                     # Test helper utilities
│
├── data/
│   └── benchmark/                   # Benchmark PDFs for parser regression testing
│
├── logs/                            # Daily pipeline logs (auto-generated)
│   └── pipeline_YYYY-MM-DD.log
│
├── scripts/
│   └── manual_checks/               # Manual verification scripts
│
└── docs/                            # Documentation (placeholder)
```

---

## Module Reference

### Core Services

| Module | Lines | Description |
|---|---|---|
| `opportunity_pipeline.py` | 936 | Main pipeline: orchestrates discovery → extraction → scoring → qualification → storage |
| `tender_parser.py` | 4,755 | Deterministic structured field extractor — the largest and most complex module |
| `scraper_search.py` | 1,923 | BFS-based web crawler for official procurement portals |
| `tender_intelligence.py` | 1,148 | Rule-based relevance analysis and service categorization |
| `document_fetcher.py` | 1,027 | Production HTTP client with retry, streaming, MIME detection |
| `tender_extraction_engine.py` | 1,078 | Master extraction pipeline coordinator |
| `html_extractor.py` | 995 | HTML → text with boilerplate removal |
| `document_cleaner.py` | 796 | Text normalization and noise removal |
| `search_router.py` | 798 | Multi-backend search orchestrator with scoring |
| `source_resolver.py` | 558 | URL resolution with PDF priority |
| `pdf_extractor.py` | 560 | PDF → text via PyMuPDF |
| `serp_search.py` | 333 | SerpAPI integration with filtering |
| `deduplication.py` | 196 | Multi-strategy deduplication |
| `search_budget.py` | 113 | SERP API budget management |

### Scoring Engine

| Module | Description |
|---|---|
| `livehooah_matcher.py` | Canonical 0.0–1.0 business relevance scorer — single source of truth for scoring |
| `relevance_classifier.py` | Experience-based classifier using regional data and keyword taxonomy |
| `experience_scoring.py` | Legacy wrapper that delegates to `livehooah_matcher` |

### Agents

| Module | Description |
|---|---|
| `tender_discovery_agent.py` | Manages 56+ base queries, query expansion, and search execution |
| `hermes_client.py` | LLM API client for Hermes/OpenRouter |
| `discovery/` | Discovery sub-module: service, query builder, response validator |

### LLM Layer

The LLM layer provides a **multi-provider fallback chain** for AI-powered tasks:

```
DeepSeek (OpenRouter) → GPT-4o-mini (OpenAI) → Laguna (Local) → Rule-Based
```

| Component | Description |
|---|---|
| `LLMRouter` | Routes prompts through the fallback chain; returns first valid response |
| `TokenGuard` | Enforces token budget (max 8,000 tokens); truncates oversized prompts |
| `Providers` | DeepSeek, GPT, Laguna, OpenRouter — each implements a `call()` method |

> **Note:** The main pipeline is entirely deterministic and does not require LLM calls. The LLM layer is available for optional qualification and intelligence enhancement.

### Google Sheets Integration

| Module | Description |
|---|---|
| `SheetsClient` | Full CRUD against Google Sheets: save opportunities, contacts, log activities, update watchlist |
| `sheets_transformer.py` | Transforms raw opportunity dicts into the 20-column Sheets schema |

### Configuration

| File | Purpose |
|---|---|
| `settings.py` | Base directory, service account path, sheet name |
| `constants.py` | Sheet names, column headers, ID prefixes, status values |
| `llm_config.py` | LLM providers, fallback chain, token limits |
| `livehooah_keywords.py` | 3-tier keyword taxonomy: `high_priority`, `engineering`, `blocked` |
| `livehooah_experience.py` | Regional experience: Tier 1 (NCR, Punjab, Haryana), Tier 2 (UP, Rajasthan), Tier 3 (Rest) |
| `official_sources.py` | 60+ official procurement sources with metadata (keywords, priority, paths, crawl depth) |

### Utilities

| Module | Description |
|---|---|
| `logger.py` | `livehooah` logger — daily rotating file + console, DEBUG level |
| `duplicate_detector.py` | Checks title+URL against existing Sheets records |
| `validators.py` | Validates title (≥5 chars), URL (http/https), email (@), opportunity (title+URL required) |
| `id_generator.py` | Sequential IDs: `OPP-000001`, `CNT-000001` |

### Infrastructure

| Module | Description |
|---|---|
| `error_handler.py` | `safe_fail()` — returns structured error response instead of crashing |

### Dashboard

| Module | Description |
|---|---|
| `app.py` | Streamlit dashboard with KPI cards, filters, qualification trends, deadline distribution, data quality metrics |
| `dashboard_data.py` | Data loading from Sheets, metric computation, filtering, and sorting |

---

## Data Flow Diagram

```
                    ┌──────────────────┐
                    │   56+ Queries    │
                    │ (tender_discovery│
                    │   _agent.py)     │
                    └────────┬─────────┘
                             │  expand_query()
                             ▼
               ┌─────────────────────────────┐
               │       SearchRouter          │
               │  ┌──────────┬──────────┐    │
               │  │ SerpAPI  │ Scraper  │    │
               │  │ (Google) │ (60+ Gov │    │
               │  │          │  Sites)  │    │
               │  └────┬─────┴────┬─────┘    │
               │       └────┬─────┘          │
               │            │ merge + dedup  │
               │            ▼                │
               │   Discovery Scoring &       │
               │   Pre-Extraction Filter     │
               │   (keyword + URL analysis)  │
               └────────────┬────────────────┘
                            │
                            ▼
               ┌─────────────────────────────┐
               │   TenderIntelligence        │
               │   (service categorization)  │
               └────────────┬────────────────┘
                            │
                            ▼
               ┌─────────────────────────────┐
               │  TenderExtractionEngine     │
               │  ┌────────────────────────┐ │
               │  │ SourceResolver         │ │
               │  │ DocumentFetcher        │ │
               │  │ PDF/HTML Extractor     │ │
               │  │ DocumentCleaner        │ │
               │  │ TenderParser           │ │
               │  └────────────────────────┘ │
               └────────────┬────────────────┘
                            │
                            ▼
               ┌─────────────────────────────┐
               │  DeduplicationService       │
               │  (URL + fingerprint + fuzzy)│
               └────────────┬────────────────┘
                            │
                            ▼
               ┌─────────────────────────────┐
               │  compute_livehooah_score()  │
               │  (0.0–1.0 relevance score)  │
               └────────────┬────────────────┘
                            │
                            ▼
               ┌─────────────────────────────┐
               │  qualify_opportunity()      │
               │  (multi-check gate)         │
               └────────────┬────────────────┘
                            │
                  ┌─────────┴─────────┐
                  │                   │
             QUALIFIED           REJECTED
                  │
                  ▼
         ┌────────────────┐
         │  Transform &   │
         │  SheetsClient  │
         │  .save()       │
         └────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌────────┐  ┌──────────┐  ┌─────────┐
│ HIGH   │  │ MEDIUM   │  │  LOW    │
│PRIORITY│  │ PRIORITY │  │PRIORITY │
└────────┘  └──────────┘  └─────────┘
```

---

## Google Sheets Schema

The system writes to the **"LIVEHOOAH Opportunity Intelligence Hub"** spreadsheet with the following sheets:

### Opportunities Sheet (20 columns)

| Column | Description |
|---|---|
| `Opportunity_ID` | Auto-generated sequential ID (e.g., `OPP-000042`) |
| `Type` | Tender type (e.g., RFP, EOI, NIT, Empanelment) |
| `Title` | Extracted tender title |
| `Organization` | Issuing organization |
| `Service_Category` | Classified category (Structural Audit, Proof Checking, etc.) |
| `Location` | Geographic location |
| `Source` | Source website/portal name |
| `Source_Link` | Direct URL to the tender document |
| `Deadline` | Submission deadline |
| `Contact_Status` | `NOT_CONTACTED` (default) |
| `Opportunity_Status` | `NEW` (default) |
| `Priority` | `HIGH` / `MEDIUM` / `LOW` (score-based) |
| `Score` | LiveHooah relevance score (0.00–1.00) |
| `Qualified` | Boolean qualification flag |
| `Qualification_Score` | Numeric qualification score |
| `Recommended_Action` | Suggested next step |
| `Qualification_Reasoning` | Detailed reasons for qualification decision |
| `Summary` | Tender summary + "WHY SELECTED" reasons |
| `Assigned_To` | Team member assignment |
| `Last_Updated` | UTC timestamp |
| `Date_Added` | UTC timestamp |

### Other Sheets

| Sheet | Purpose |
|---|---|
| `Contacts` | Contact information linked to opportunities |
| `Keywords` | Keyword configuration |
| `Activity_Log` | Pipeline run logs (timestamp, agent, action, records_added, notes) |
| `Existing_Client_Watchlist` | Existing client tracking and alerts |
| `HIGH_PRIORITY` | High-priority opportunity routing |
| `MEDIUM_PRIORITY` | Medium-priority opportunity routing |
| `LOW_PRIORITY` | Low-priority opportunity routing |

---

## Configuration Reference

### LiveHooah Keywords (`config/livehooah_keywords.py`)

Three-tier keyword taxonomy:

- **`high_priority`** — Core business signals (structural engineering, warehouse, PEB, high-rise, etc.)
- **`engineering`** — Secondary signals (seismic design, foundation design, IS code, etc.)
- **`blocked`** — Hard block list (road, highway, airport, dam, solar, railway, etc.)

### Official Sources (`config/official_sources.py`)

60+ official procurement sources organized by category:

- **Government** — CPWD, eprocure.gov.in, GEM, IREPS
- **Municipal** — Municipal corporations (Delhi, Lucknow, Chandigarh, etc.)
- **Development Authorities** — DDA, NOIDA Authority, HUDA
- **Academic** — IIT Delhi, IIT Bombay, IIT Kharagpur, AIIMS
- **Public Sector** — NBCC, NHPC, BEL, HAL
- **Smart Cities** — Various Smart City SPVs

Each source defines: name, URL, keywords, category, services, sectors, priority (1–10), crawl_depth, and tender paths.

### LLM Fallback Chain (`config/llm_config.py`)

```
DeepSeek (OpenRouter) → GPT-4o-mini (OpenAI) → Laguna (Local) → Rule-Based
```

Token limit: 8,000 tokens max.

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | API key for OpenRouter (Hermes + DeepSeek) | — |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to Google service account JSON | `service.json` |
| `GOOGLE_SHEET_ID` | Google Sheets spreadsheet ID | — |
| `SERPAPI_KEY` | SerpAPI key for Google Search | — |
| `MAX_HERMES_TOKENS` | Max tokens for Hermes calls | `300` |
| `MAX_GPT_TOKENS` | Max tokens for GPT calls | `800` |
| `SERP_DAILY_REQUEST_LIMIT` | Daily SERP API call budget | `12` |

---

## Installation & Setup

### Prerequisites

- Python 3.10+
- Google Cloud Service Account with Sheets API access
- SerpAPI account (for Google Search)
- OpenRouter API key (optional — for LLM features)

### Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd livehooah_tender_system

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
# Copy .env.example to .env and fill in your API keys
# Place your Google service_account.json in config/

# 5. Verify setup
python -c "from config.settings import BASE_DIR; print(f'Base: {BASE_DIR}')"
```

### Key Dependencies

| Package | Purpose |
|---|---|
| `gspread` | Google Sheets API client |
| `google-auth` | Google service account authentication |
| `requests` | HTTP client for document fetching |
| `beautifulsoup4` + `lxml` | HTML parsing |
| `pymupdf (fitz)` | PDF text extraction |
| `python-dotenv` | Environment variable loading |
| `google-search-results` | SerpAPI client |
| `pandas` | Data manipulation (dashboard) |
| `streamlit` | Dashboard UI |

---

## Running the Pipeline

### Daily Pipeline

```bash
python main.py
```

This executes the full discovery → extraction → scoring → qualification → storage pipeline for all 56+ base queries.

### Expected Output

```
Pipeline Complete | Query=structural consultant | Qualified=3 | Saved=2 | Duplicates=1 | Failed=0
```

### Logs

Pipeline logs are written to `logs/pipeline_YYYY-MM-DD.log` with full diagnostic detail:

```
2026-10-05 13:00:01 | INFO | livehooah | Starting pipeline for query: structural consultant
2026-10-05 13:00:02 | INFO | livehooah | SERP raw results | query=structural consultant | count=18
2026-10-05 13:00:03 | INFO | livehooah | Scraper raw results | query=structural consultant | count=12
2026-10-05 13:00:04 | INFO | livehooah | Discovery dedup diagnostics | combined=30 | deduplicated=24
2026-10-05 13:00:05 | INFO | livehooah | QUALIFIED | Score=0.78 | Selection of Structural Consultant for...
```

---

## Running the Dashboard

```bash
cd dashboard
streamlit run app.py
```

The dashboard provides:

- **KPI Cards** — Total opportunities, qualified count, high-priority count, upcoming deadlines
- **Opportunity Table** — Sortable, filterable table with all opportunity details
- **Qualification Trends** — Time-series visualization of qualification rates
- **Priority Distribution** — Breakdown of HIGH/MEDIUM/LOW priority opportunities
- **Deadline Distribution** — Timeline of upcoming deadlines
- **Data Quality Metrics** — Extraction confidence, field completeness analysis
- **Daily Run Audit** — Pipeline health monitoring with per-run statistics

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_livehooah_matcher.py

# Run specific test
pytest tests/test_tender_parser.py::TestTenderParser::test_parse_basic
```

The test suite includes **38 test files** covering:

- LiveHooah relevance scoring edge cases
- Tender parser extraction accuracy
- Pipeline extraction handoff contracts
- Search router filtering and scoring
- Document fetcher retry behavior
- HTML/PDF extraction quality
- Dashboard data computation
- Sheets client caching and deduplication
- Source resolver priority logic
- Validator and utility functions

---

## Design Principles

1. **Deterministic over Probabilistic** — All scoring, parsing, and qualification logic is rule-based. No LLM calls in the critical pipeline path ensures consistent, reproducible results.

2. **Separation of Concerns** — Each module has a single, well-defined responsibility. Discovery doesn't parse. Parsing doesn't score. Scoring doesn't qualify. Qualification doesn't store.

3. **Defense in Depth** — Multiple filtering and validation layers catch bad data at every stage: discovery filtering → extraction validation → document validation → parse validation → qualification.

4. **Graceful Degradation** — LLM fallback chain (DeepSeek → GPT → Laguna → Rule-Based). SERP budget management disables paid search on failure. Safe-fail error handling prevents pipeline crashes.

5. **Cost Control** — `SearchBudget` and `ScopedSearchBudget` enforce per-run and per-query SERP API limits. Token guard enforces LLM token budgets.

6. **No Aggregator Dependency** — The system directly crawls 60+ official government procurement portals rather than relying on commercial tender aggregators.

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Web Scraping** | `requests`, `beautifulsoup4`, `lxml` |
| **PDF Processing** | `PyMuPDF (fitz)` |
| **Search API** | SerpAPI (Google Search) |
| **Storage** | Google Sheets (via `gspread`) |
| **Authentication** | Google Service Account (`google-auth`) |
| **LLM Providers** | OpenRouter (DeepSeek, Hermes), OpenAI (GPT-4o-mini) |
| **Dashboard** | Streamlit + Pandas |
| **Testing** | Pytest |
| **Logging** | Python `logging` with daily rotation |
| **Config** | `python-dotenv` for environment variables |

---

*Built for LiveHooah Structural Engineering Consultancy.*
]]>
