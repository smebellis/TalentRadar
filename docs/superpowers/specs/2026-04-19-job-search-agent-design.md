# Job Search Agent — Design Spec
**Date:** 2026-04-19
**Status:** Approved

---

## 1. Purpose

A modular Python pipeline driven by user input — provided via the command line (and later through the A2UI interface) — that finds jobs matching the user's resume, scores them for fit, identifies relevant contacts at high-scoring companies, generates personalized LinkedIn outreach messages, persists all results to PostgreSQL, and renders output via A2UI. Runs on-demand via CLI or on a schedule.

---

## 2. Goals & Non-Goals

**Goals:**
- Search Google (via Claude) and LinkedIn (via Apify) for jobs posted in the last 24 hours
- Score jobs 0–10 against a parsed resume profile; surface only top 10 scoring >7
- Find internal recruiters, hiring managers, peers, and veterans at high-scoring companies
- Prioritize veteran contacts when the searcher is identified as a veteran (inferred from resume)
- Generate personalized LinkedIn connection messages (<300 chars) per contact
- Persist jobs, contacts, and messages to PostgreSQL via Pydantic-modelled schemas
- Render all output as A2UI JSON
- Support CLI (manual) and scheduled execution
- Use Hydra for all configuration; no hardcoded values

**Non-Goals:**
- Auto-applying to jobs
- Notion integration (replaced by PostgreSQL)
- Reslink video URLs
- External recruiter or agency contacts
- Integration tests in CI (run separately)

---

## 3. Architecture

### Data Flow

```
CLI / Scheduler
  → Orchestrator (loads Hydra config)
      → CV Loader → CV Parser → ResumeProfile (incl. is_veteran inference)
      → [Google Search ∥ LinkedIn Search] (with SearchFilters)
      → Combiner (merge + deduplicate)
      → Job Scorer → filter score >7, top 10, sort by recency then score
      → JobRepository.save()
      → Contact Finder → Contact Scorer → filter score ≥7
      → ContactRepository.save()
      → Message Generator
      → A2UI Renderer → output
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `llm/protocol.py` | `LLMClient` Protocol — model-agnostic interface |
| `llm/claude.py` | Claude implementation of `LLMClient` |
| `cv/loader.py` | Load PDF resume via `pymupdf` → raw text |
| `cv/parser.py` | LLM prompt → structured `ResumeProfile` (infers `is_veteran`) |
| `search/filters.py` | `SearchFilters` Pydantic model: keywords, location, time_window_hours |
| `search/google.py` | Claude web search tool → job listings |
| `search/linkedin.py` | Apify LinkedIn scraper → job listings |
| `pipeline/combiner.py` | Merge + deduplicate results from both sources |
| `pipeline/state.py` | `PipelineState` enum + `PipelineContext` dataclass |
| `pipeline/orchestrator.py` | Coordinates all stages, manages state transitions, error handling |
| `scoring/job_scorer.py` | Score jobs 0–10 against `ResumeProfile` via LLM |
| `scoring/contact_scorer.py` | Score contacts 0–10; applies veteran relevance boost |
| `contacts/finder.py` | Apify + Vibe Prospecting; finds 4 categories: Veterans, Hiring Managers, Recruiters, Peers |
| `messaging/generator.py` | Personalized LinkedIn messages per contact (<300 chars) |
| `db/models/` | Pydantic models: `Job`, `Contact`, `Message`, `ResumeProfile` |
| `db/repositories/` | `JobRepository`, `ContactRepository` — asyncpg |
| `db/connection.py` | asyncpg connection pool setup |
| `ui/renderer.py` | Emit A2UI JSON for job table, contact table, messages, priority summary |
| `utils/logger.py` | `get_logger(name)` factory used app-wide |
| `cli.py` | Entry point — modes: `search`, `full`, `contacts-only` |
| `scheduler.py` | Wraps orchestrator for cron/scheduled runs |

---

## 4. Folder Structure

```
job_search_agent/
├── config/
│   ├── api_keys.yaml          # Anthropic, Apify, Vibe Prospecting, Postgres
│   ├── database.yaml          # Postgres connection settings
│   ├── logging.yaml           # Log level, format, file handler path
│   ├── scoring.yaml           # Score thresholds, top-N limits
│   └── search.yaml            # Location, keywords, remote/onsite, time window
│
├── cv/
│   ├── loader.py              # pymupdf PDF → raw text
│   └── parser.py              # LLM prompt → ResumeProfile (incl. is_veteran)
│
├── db/
│   ├── connection.py          # asyncpg pool setup
│   ├── models/
│   │   ├── contact.py         # Pydantic Contact model
│   │   ├── job.py             # Pydantic Job model
│   │   ├── message.py         # Pydantic Message model
│   │   └── resume.py          # Pydantic ResumeProfile model
│   └── repositories/
│       ├── contact_repo.py
│       └── job_repo.py
│
├── contacts/
│   └── finder.py              # Apify + Vibe Prospecting; 4 categories + veteran logic
│
├── llm/
│   ├── claude.py              # Claude implementation of LLMClient
│   └── protocol.py            # LLMClient Protocol (model-agnostic)
│
├── messaging/
│   └── generator.py           # Personalized LinkedIn messages
│
├── pipeline/
│   ├── combiner.py            # Merge + deduplicate search results
│   ├── orchestrator.py        # Stage coordination + state transitions
│   └── state.py               # PipelineState enum + PipelineContext
│
├── scoring/
│   ├── contact_scorer.py      # Score contacts 0-10; veteran boost
│   └── job_scorer.py          # Score jobs 0-10 against ResumeProfile
│
├── search/
│   ├── filters.py             # SearchFilters Pydantic model
│   ├── google.py              # Claude web search → job listings
│   └── linkedin.py            # Apify LinkedIn scraper → job listings
│
├── ui/
│   └── renderer.py            # A2UI JSON output
│
├── utils/
│   └── logger.py              # get_logger(name) factory
│
├── tests/
│   ├── integration/
│   │   └── test_pipeline.py   # Real API calls; run separately, not in CI
│   └── unit/
│       ├── test_combiner.py
│       ├── test_contact_finder.py
│       ├── test_contact_scorer.py
│       ├── test_cv_loader.py
│       ├── test_cv_parser.py
│       ├── test_google_search.py
│       ├── test_job_scorer.py
│       ├── test_linkedin_search.py
│       ├── test_message_generator.py
│       ├── test_orchestrator.py
│       ├── test_repositories.py
│       └── test_ui_renderer.py
│
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-19-job-search-agent-design.md
│
├── cli.py                     # Entry point
├── scheduler.py               # Scheduled execution wrapper
├── .env.example
├── requirements.txt
└── README.md
```

---

## 5. Pydantic Models & Data Contracts

No raw dicts cross module boundaries. Every stage receives and returns typed models.

```
ResumeProfile
  - skills: list[str]
  - experience_years: int
  - seniority: str
  - location: str
  - is_veteran: bool          # inferred by LLM parser prompt, never hardcoded
  - summary: str

SearchFilters
  - keywords: list[str]
  - location: str             # default: "Denver, CO"
  - remote: bool
  - onsite: bool
  - job_type: str             # full-time | part-time | contract
  - time_window_hours: int    # default: 24

Job
  - id: UUID
  - title: str
  - company: str
  - posted_at: datetime
  - source: str               # "google" | "linkedin"
  - apply_url: str
  - raw_description: str
  - fit_score: float | None

Contact
  - id: UUID
  - name: str
  - title: str
  - company: str
  - category: str             # "veteran" | "hiring_manager" | "recruiter" | "peer"
  - linkedin_url: str
  - email: str | None
  - relevance_score: float
  - is_veteran: bool
  - notes: str                # <100 chars

Message
  - contact_id: UUID
  - job_id: UUID
  - message_text: str         # <300 chars
  - character_count: int

PipelineContext
  - resume: ResumeProfile
  - filters: SearchFilters
  - jobs: list[Job]
  - contacts: list[Contact]
  - messages: list[Message]
  - state: PipelineState
  - errors: list[str]
```

---

## 6. Contact Discovery & Veteran Logic

`contacts/finder.py` identifies 4 categories per high-scoring job (score >7):

| Category | Description | Max per job |
|---|---|---|
| Veterans | Currently employed; identified via military service signals on LinkedIn | 5–8 |
| Hiring Managers | Likely direct manager for the role | 5–8 |
| Recruiters | Internal talent team only (no agencies) | 5–8 |
| Peers | Same function, similar seniority | 5–8 |

**Sort order when `is_veteran=True`:** Veterans → Hiring Managers → Recruiters → Peers

**Sort order when `is_veteran=False`:** Hiring Managers → Recruiters → Peers (veterans still found but not elevated)

`contact_scorer.py` applies a relevance boost to veteran contacts when the searcher is also a veteran.

---

## 7. Veteran Inference

`is_veteran` is inferred entirely by the CV parser LLM prompt. The prompt instructs Claude to look for:
- Military branch mentions (Army, Navy, Marines, Air Force, Coast Guard, Space Force)
- Ranks, military titles, MOS/AFSC codes
- Deployment language, transition language ("separated", "ETS", "honorable discharge")
- Military education (ROTC, service academies)
- Veteran service organizations

Default: `False` if no signals found. The code reads the structured output — inference logic lives only in the prompt.

---

## 8. Output

**Job Table** (top 10, score >7, sorted by recency then score):
`# | Role | Company | Posted | Source | Fit Score | Apply Link`

**Contact Table** (per high-scoring job, score ≥7, sorted by relevance):
`# | Name | Title | Category | Relevance Score | LinkedIn URL | Email | Notes`

**Priority Outreach Summary:** ranked list with persona, name, and why to reach out

**LinkedIn Messages:** one per contact, <300 chars, personalized to a specific profile detail

All output rendered as A2UI JSON via `ui/renderer.py`.

---

## 9. Configuration (Hydra)

| File | Contents |
|---|---|
| `config/api_keys.yaml` | Anthropic, Apify, Vibe Prospecting, Postgres credentials |
| `config/search.yaml` | location, keywords, remote, onsite, time_window_hours |
| `config/scoring.yaml` | job_score_threshold (7), contact_score_threshold (7), top_n_jobs (10), max_contacts_per_category (8) |
| `config/database.yaml` | host, port, db name, pool settings |
| `config/logging.yaml` | level, format, handlers (console + rotating file) |

---

## 10. Logging

- `utils/logger.py` exports `get_logger(name)` — every module calls `logger = get_logger(__name__)`
- Logging config managed by Hydra via `config/logging.yaml`
- Unit tests assert `caplog` output only for: error states, failed API calls, dropped jobs, critical state transitions
- Routine `INFO` logs are not tested

---

## 11. Testing Strategy

**TDD order** (dependency depth, shallowest first):
1. Pydantic models (`db/models/`)
2. `llm/protocol.py` + `llm/claude.py`
3. `cv/loader.py` → `cv/parser.py`
4. `search/filters.py` → `search/google.py` → `search/linkedin.py`
5. `pipeline/combiner.py`
6. `scoring/job_scorer.py` → `scoring/contact_scorer.py`
7. `contacts/finder.py`
8. `messaging/generator.py`
9. `db/repositories/`
10. `pipeline/orchestrator.py`
11. `ui/renderer.py`

**Mocking approach:** import-style mocking (`unittest.mock.patch("module.ClassName")`), not from-import style — avoids the mock ordering bugs from take 1.

**Integration tests:** `tests/integration/test_pipeline.py` — real API calls, run manually, never in CI by default.

---

## 12. CLI Modes

```
python cli.py search        # Search + score jobs only
python cli.py full          # Full pipeline: jobs + contacts + messages
python cli.py contacts-only # Re-run contact discovery on saved jobs
```

Scheduler wraps `full` mode on a configurable cron interval via `scheduler.py`.

---

## 13. Key Lessons Applied from Take 1

| Lesson | Applied As |
|---|---|
| Class-vs-instance attribute bugs | Pydantic models enforce types at construction |
| Mock ordering confusion | Consistent import-style mocking documented in test strategy |
| Wrong data source (raw vs scored) | No raw dicts cross boundaries — typed models only |
| Wrong abstraction layer | Each module owns exactly one responsibility |
| LLMClient not model-agnostic | `llm/protocol.py` Protocol from day one |
| Token overuse | Strict top-10 cap; Claude only called where necessary |
