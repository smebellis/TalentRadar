# Streamlit Web UI — Design Spec

**Date:** 2026-05-05  
**Goal:** Make the job search pipeline accessible to a non-technical friend — upload a resume, fill in a form, click Run.

---

## Problem

The current interface requires terminal familiarity: a multi-step `.env` setup, a long `docker compose exec` command, and YAML config editing. A friend who is job hunting but not technical cannot use it without hand-holding.

---

## Target User

A friend who is job hunting. Comfortable installing Docker Desktop and opening a browser. Not comfortable with terminals, YAML files, or long CLI commands.

---

## User Journey (after setup)

1. Download the repo ZIP from GitHub (no git needed)
2. Install Docker Desktop
3. Open a terminal, `cd` into the folder, run `docker compose up --build -d` (one-time)
4. Open `http://localhost:8501` in their browser
5. Upload resume PDF, type location and keywords, click **Find My Jobs**
6. Wait ~2–3 minutes for results to appear on screen

The `.env` file is committed to the repo with API keys pre-filled — the friend never touches it.

---

## Architecture

### New files

| Path | Purpose |
|---|---|
| `web/app.py` | Streamlit application |
| `web/__init__.py` | Package marker |

### Modified files

| Path | Change |
|---|---|
| `docker-compose.yml` | Add `web` service |
| `requirements.txt` | Add `streamlit` |
| `cli.py` | Add `--no-ui` flag to `full` mode |
| `.env` | Pre-fill with shared API keys (committed) |

### Services

The `web` service is built from the same `Dockerfile` as `app` (same Python environment, same codebase). It runs a different command: `streamlit run web/app.py`. No new image needed.

```
┌─────────────────────────────────────────────┐
│  Docker Compose                             │
│                                             │
│  ┌──────────┐   ┌──────────┐   ┌────────┐  │
│  │   web    │   │   app    │   │   db   │  │
│  │ :8501    │   │  (CLI)   │   │ :5432  │  │
│  │Streamlit │   │ optional │   │Postgres│  │
│  └────┬─────┘   └──────────┘   └───┬────┘  │
│       │                            │       │
│       └────────────────────────────┘       │
│              shared network                │
└─────────────────────────────────────────────┘
```

Shared volumes between `web` and host:
- `./config:/app/config` — so Streamlit can update `search.yaml`
- `./output:/app/output` — so `output.json` lands on the host

---

## Streamlit UI

Single-page layout. No tabs. Three inputs and one button.

### Inputs

| Input | Type | Default |
|---|---|---|
| Upload your resume | `st.file_uploader` (PDF only) | — |
| Where are you looking? | `st.text_input` | `"Denver, CO"` |
| What kind of jobs? | `st.text_input` (comma-separated) | `""` |

The **Find My Jobs** button is disabled until a resume file is uploaded.

### While running

- Spinner: `"Searching for jobs… this takes 2–3 minutes"`
- No live streaming — results appear all at once when complete

### Results (three expandable sections)

**Top Jobs**

Rendered as a table: Title, Company, Score, Apply (link).

**Contacts**

Rendered as a table: Name, Title, Company, Category, Score, LinkedIn (clickable profile link). LinkedIn URL rendered as a hyperlink using `st.markdown` or Streamlit's dataframe link column — consistent with the TUI "Profile" link behavior.

**Outreach Messages**

Each message in its own `st.text_area` (read-only, copyable). Grouped under the contact's name.

---

## Data Flow

```
User uploads PDF
       │
       ▼
Streamlit saves → /tmp/resume.pdf
       │
Streamlit patches `search.location` in config/search.yaml using PyYAML (load → update key → dump), leaving all other fields intact
       │
       ▼
subprocess.run([
  "python", "cli.py", "full",
  "--cv", "/tmp/resume.pdf",
  "--keywords", kw1, kw2, ...  # keywords split on comma, whitespace-stripped
  "--no-ui"
])
       │
       ▼ (pipeline runs, writes output/output.json)
       │
Streamlit reads output/output.json
       │
       ▼
Renders Jobs / Contacts / Messages
```

### `--no-ui` flag

Add a `--no-ui` argument to `cli.py`. When present in `full` mode, skip `JobSearchApp` and call `asyncio.run(run_full(cfg, cv_path, keywords))` directly. The `run_full()` function already exists and handles the full pipeline headlessly.

---

## Error Handling

- If subprocess exits with non-zero code: show `st.error("Something went wrong. Check that your API keys are valid and try again.")`
- If `output.json` is missing or malformed: show `st.warning("No results found. Try different keywords or a broader location.")`
- If resume upload is not a PDF: `st.file_uploader` restricts to `type=["pdf"]` — no extra validation needed

---

## What Is NOT in Scope

- Live pipeline progress / streaming output
- Job listing → contacts-only flow (planned future feature)
- Authentication or multi-user support
- Mobile layout optimization

---

## Open Questions (resolved)

| Question | Decision |
|---|---|
| How does Streamlit trigger the pipeline? | `subprocess.run` with `--no-ui` flag — clean separation |
| Where does the resume go? | `/tmp/resume.pdf` inside the `web` container |
| How are API keys distributed? | `.env` committed to repo with pre-filled keys |
| Does the TUI need to work from Streamlit? | No — `--no-ui` flag bypasses it entirely |
