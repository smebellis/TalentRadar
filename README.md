# Job Search Agent

A modular Python pipeline that automates job hunting. It searches Google and LinkedIn, scores results against your resume, discovers contacts at top companies, and generates personalized LinkedIn outreach messages — all from a single CLI command.

## What It Does

1. **Parses your resume** — extracts skills, experience, seniority, and veteran status via LLM
2. **Searches for jobs** — Google (Claude web search) and LinkedIn (Apify) run in parallel
3. **Scores each job** — LLM rates fit 0–10 against your resume profile
4. **Finds contacts** — hiring managers, recruiters, veterans, and peers at top companies
5. **Scores contacts** — ranks by relevance with a veteran boost
6. **Generates outreach** — personalized LinkedIn messages under 300 characters
7. **Persists results** — stores everything to PostgreSQL
8. **Renders output** — writes `output.json` to disk after every run

---

## Quickstart (Docker — recommended)

Docker is the easiest way to run the pipeline. No local Python or PostgreSQL install required.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine + Compose v2

> **WSL2 users:** the Docker daemon does not auto-start. Run this before any `docker` command:
> ```bash
> sudo dockerd > /tmp/dockerd.log 2>&1 &
> ```

### 1. Clone the repo

```bash
git clone <repo-url>
cd job_search_agent_take_2
```

### 2. Configure your environment

```bash
cp .env.example .env
```

Open `.env` and fill in every value:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Get from [console.anthropic.com](https://console.anthropic.com) |
| `APIFY_API_TOKEN` | Get from [apify.com](https://apify.com) — used for LinkedIn job scraping and contact search |
| `VIBE_API_KEY` | Get from [explorium.ai](https://explorium.ai) — used for contact enrichment (optional; pipeline degrades gracefully without it) |
| `POSTGRES_HOST` | Set to `db` when using Docker |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_DB` | `job_search` |
| `POSTGRES_USER` | Any username, e.g. `jobsearch` |
| `POSTGRES_PASSWORD` | Any strong password |
| `RESUME_DIR` | Absolute path to the folder containing your resume PDF, e.g. `/home/yourname/resumes` |

### 3. Configure your search

Edit `config/search.yaml` to set your target location and keywords:

```yaml
search:
  location: "Denver, CO"       # Target city / region
  keywords: []                 # Overridden by --keywords flag at runtime
  remote: true                 # Include remote roles
  onsite: true                 # Include onsite roles
  job_type: "full-time"
  time_window_hours: 168       # Look back this many hours (168 = 1 week)
```

Score thresholds and contact caps are in `config/scoring.yaml`:

```yaml
scoring:
  job_score_threshold: 7.0        # Only keep jobs scored >= this
  contact_score_threshold: 7.0    # Only keep contacts scored >= this
  top_n_jobs: 10                  # Max jobs to process contacts for
  max_contacts_per_category: 8    # Max contacts per type (recruiter, peer, etc.)
  veteran_score_boost: 1.5        # Extra score added for veteran contacts
```

### 4. Build and start

```bash
docker compose up --build -d
```

### 5. Run the pipeline

```bash
docker compose exec app python cli.py full \
  --cv /data/your_resume.pdf \
  --keywords "Python" "Data Engineering"
```

Replace `your_resume.pdf` with the filename of your resume inside `RESUME_DIR`.  
The `--keywords` flag overrides the defaults in `config/search.yaml`.

The TUI launches automatically and shows live progress across four panels:

- **Progress** — current pipeline stage
- **Jobs** — top-scoring jobs as they are found
- **Contacts** — ranked contacts at those companies
- **Messages** — generated LinkedIn outreach for each contact

Press `q` to exit the TUI when the pipeline completes.

### 6. Access your results

**Output file** — written to the project root after every run:
```bash
cat output.json | python -m json.tool | less
```

**Database** — query past runs any time:
```bash
docker compose exec db psql -U jobsearch -d job_search
```

Useful queries:

```sql
-- Top scoring jobs
SELECT title, company, fit_score, apply_url
FROM jobs
ORDER BY fit_score DESC
LIMIT 20;

-- Contacts with their outreach messages
SELECT c.name, c.title, c.company, c.category, m.message_text
FROM contacts c
LEFT JOIN messages m ON m.contact_id = c.id
ORDER BY c.relevance_score DESC;

-- Row counts
SELECT
  (SELECT COUNT(*) FROM jobs)     AS jobs,
  (SELECT COUNT(*) FROM contacts) AS contacts,
  (SELECT COUNT(*) FROM messages) AS messages;
```

### Stop

```bash
docker compose down          # Stop containers, keep database volume
docker compose down -v       # Stop containers AND wipe the database
```

---

## Local Setup (without Docker)

If you prefer to run without Docker you need Python 3.11+ and a running PostgreSQL instance.

```bash
# Install dependencies
uv sync

# Copy and fill in your environment
cp .env.example .env
# Set POSTGRES_HOST=localhost and fill in your local DB credentials

# Run
python cli.py full --cv path/to/resume.pdf --keywords "Python" "Data Engineering"
```

---

## Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ -v --cov=. --cov-report=term-missing --ignore=tests/integration

# Integration tests (requires real API keys and a running database)
pytest tests/integration/ -v
```

---

## Project Structure

```
cli.py              Entry point
cv/                 Resume loading (PDF) and parsing (LLM)
search/             Google and LinkedIn job searchers + filters
pipeline/           Orchestrator and pipeline state machine
scoring/            Job and contact scorers (LLM-driven, 0–10)
contacts/           Contact discovery via Apify + Vibe Prospecting
messaging/          Personalized LinkedIn message generator
db/                 asyncpg connection, schema, and repositories
ui/                 Textual TUI + A2UI JSON renderer
llm/                LLMClient protocol + Claude implementation
utils/              Logger factory
config/             Hydra YAML configuration
tests/              Unit and integration test suites
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| `anthropic` | LLM client (Claude) |
| `apify-client` | LinkedIn job scraper and contact finder |
| `asyncpg` | Async PostgreSQL driver |
| `pydantic` v2 | All data models — no raw dicts cross module boundaries |
| `hydra-core` | YAML configuration management |
| `pymupdf` | PDF resume text extraction |
| `textual` | Terminal UI |
| `pytest` + `pytest-asyncio` | Test suite |

---

## License

MIT
