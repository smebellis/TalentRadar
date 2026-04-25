# Job Search Agent

A modular Python pipeline that automates Denver-area job hunting. It searches Google and LinkedIn, scores results against your resume, discovers contacts at top companies, and generates personalized LinkedIn outreach messages — all from a single CLI command.

## What It Does

1. **Parses your resume** — extracts skills, experience, seniority, and veteran status via LLM
2. **Searches for jobs** — Google (Claude web search) and LinkedIn (Apify) run in parallel
3. **Scores each job** — LLM rates fit 0–10 against your resume profile
4. **Finds contacts** — hiring managers, recruiters, veterans, and peers at top companies
5. **Scores contacts** — ranks by relevance with a veteran boost
6. **Generates outreach** — personalized LinkedIn messages under 300 characters
7. **Persists results** — stores everything to PostgreSQL
8. **Renders output** — A2UI JSON for downstream rendering

## Requirements

- Python 3.11+
- PostgreSQL
- API keys: Anthropic, Apify, Vibe Prospecting

## Setup

```bash
# Install dependencies
uv sync

# Copy and fill in your API keys
cp .env.example .env
```

## Usage

```bash
# Full pipeline — search, score, find contacts, generate messages
python cli.py full --cv path/to/resume.pdf --keywords "Python" "Data Engineering"

# Search and score jobs only
python cli.py search --cv path/to/resume.pdf

# Contact discovery only
python cli.py contacts-only --cv path/to/resume.pdf
```

## Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=. --cov-report=term-missing --ignore=tests/integration

# Integration tests (requires real API keys)
pytest tests/integration/ -v
```

## Project Structure

```
cv/             Resume loading (PDF) and parsing (LLM)
search/         Google and LinkedIn job searchers + filters
pipeline/       Combiner, orchestrator, and pipeline state
scoring/        Job and contact scorers (LLM-driven, 0–10)
contacts/       Contact discovery via Apify + Vibe Prospecting
messaging/      Personalized LinkedIn message generator
db/             asyncpg connection pool and repositories
ui/             A2UI JSON renderer
llm/            LLMClient protocol + Claude implementation
utils/          Logger factory
config/         Hydra YAML configuration
```

## Configuration

All settings live in `config/`. No hardcoded values anywhere.

| File | Controls |
|---|---|
| `config/search.yaml` | Location, keywords, remote/onsite, time window |
| `config/scoring.yaml` | Score thresholds, top-N caps, veteran boost |
| `config/database.yaml` | PostgreSQL connection pool settings |
| `config/logging.yaml` | Log level and handlers |

## Tech Stack

- **anthropic SDK** — LLM client (Claude)
- **apify-client** — LinkedIn job scraper and contact finder
- **asyncpg** — async PostgreSQL driver
- **Pydantic v2** — all data models; no raw dicts cross module boundaries
- **Hydra-core** — configuration management
- **pymupdf** — PDF resume text extraction
- **pytest + pytest-asyncio** — test suite

## License

MIT
