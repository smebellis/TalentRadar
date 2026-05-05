# Streamlit Web UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Streamlit web UI so a non-technical friend can upload a resume, fill in a form, and run the full pipeline from a browser.

**Architecture:** A `web/` package holds a Streamlit app (`app.py`) plus two helper modules (`config_writer.py`, `results.py`). A new `web` Docker service is built from the same `Dockerfile` and exposes port 8501. The pipeline is triggered headlessly via a new `--no-ui` flag on `cli.py full`.

**Tech Stack:** Python 3.12, Streamlit, PyYAML, subprocess, Docker Compose

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `requirements.txt` | Modify | Add `streamlit` |
| `cli.py` | Modify | Add `--no-ui` flag to bypass TUI |
| `web/__init__.py` | Create | Package marker |
| `web/config_writer.py` | Create | Patch `search.location` in `config/search.yaml` |
| `web/results.py` | Create | Parse `output.json` into job/contact lists |
| `web/app.py` | Create | Streamlit UI: form, subprocess trigger, result display |
| `docker-compose.yml` | Modify | Add `web` service on port 8501 |
| `.gitignore` | Modify | Remove `.env` so pre-filled keys can be committed |
| `.env` | Modify | Set `POSTGRES_HOST=db`, pre-fill API keys |
| `tests/unit/test_cli_no_ui.py` | Create | Tests for `--no-ui` flag |
| `tests/unit/test_web_config_writer.py` | Create | Tests for config patching |
| `tests/unit/test_web_results.py` | Create | Tests for output.json parsing |

---

## Task 1: Add `streamlit` to requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add streamlit to requirements.txt**

Open `requirements.txt` and add this line at the end:

```
streamlit>=1.35.0
```

- [ ] **Step 2: Commit**

```bash
git add requirements.txt
git commit -m "chore: add streamlit dependency"
```

---

## Task 2: Add `--no-ui` flag to `cli.py`

**Files:**
- Modify: `cli.py`
- Create: `tests/unit/test_cli_no_ui.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_cli_no_ui.py`:

```python
import sys
from unittest.mock import MagicMock, patch

import pytest


def test_no_ui_flag_runs_headless(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "full", "--cv", "/tmp/resume.pdf", "--no-ui"])

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=None)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    with patch("cli.initialize", return_value=mock_ctx), \
         patch("cli.compose", return_value=MagicMock()), \
         patch("asyncio.run") as mock_async_run, \
         patch("cli.JobSearchApp") as mock_app:
        from cli import main
        main()

    mock_async_run.assert_called_once()
    mock_app.assert_not_called()


def test_without_no_ui_flag_launches_tui(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["cli.py", "full", "--cv", "/tmp/resume.pdf"])

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=None)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    mock_app_instance = MagicMock()

    with patch("cli.initialize", return_value=mock_ctx), \
         patch("cli.compose", return_value=MagicMock()), \
         patch("asyncio.run") as mock_async_run, \
         patch("cli.JobSearchApp", return_value=mock_app_instance) as mock_app_cls:
        from cli import main
        main()

    mock_app_cls.assert_called_once()
    mock_app_instance.run.assert_called_once()
    mock_async_run.assert_not_called()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_cli_no_ui.py -v
```

Expected: `FAILED` — `unrecognized arguments: --no-ui`

- [ ] **Step 3: Add `--no-ui` flag to `cli.py`**

In `cli.py`, update the `main()` function. Add the argument and add the `--no-ui` branch:

```python
def main():
    parser = argparse.ArgumentParser(description="Job Search Agent")
    parser.add_argument(
        "mode", choices=["search", "full", "contacts-only"], help="Pipeline mode"
    )
    parser.add_argument("--cv", required=True, help="Path to resume PDF")
    parser.add_argument("--keywords", nargs="*", default=[], help="Search keywords")
    parser.add_argument("--no-ui", action="store_true", help="Run without TUI")
    args = parser.parse_args()

    with initialize(config_path="config", version_base=None):
        cfg = compose(config_name="config")

    if args.mode == "full":
        if args.no_ui:
            asyncio.run(run_full(cfg, cv_path=args.cv, keywords=args.keywords))
        else:
            app = JobSearchApp(cfg=cfg, cv_path=args.cv, keywords=args.keywords)
            app.run()
    else:
        logger.info(f"Mode '{args.mode}' not yet implemented — use 'full'")
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/unit/test_cli_no_ui.py -v
```

Expected: both tests `PASSED`

- [ ] **Step 5: Run full unit suite to check for regressions**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add cli.py tests/unit/test_cli_no_ui.py
git commit -m "feat: add --no-ui flag to cli.py full mode for headless pipeline runs"
```

---

## Task 3: Create `web/config_writer.py`

**Files:**
- Create: `web/__init__.py`
- Create: `web/config_writer.py`
- Create: `tests/unit/test_web_config_writer.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_web_config_writer.py`:

```python
from pathlib import Path
import yaml
import pytest

from web.config_writer import update_location


def test_update_location_changes_only_location(tmp_path):
    config_file = tmp_path / "search.yaml"
    config_file.write_text(
        "search:\n"
        "  location: 'Denver, CO'\n"
        "  remote: true\n"
        "  keywords: []\n"
    )

    update_location("Austin, TX", config_path=config_file)

    result = yaml.safe_load(config_file.read_text())
    assert result["search"]["location"] == "Austin, TX"
    assert result["search"]["remote"] is True
    assert result["search"]["keywords"] == []


def test_update_location_overwrites_previous_value(tmp_path):
    config_file = tmp_path / "search.yaml"
    config_file.write_text("search:\n  location: 'Denver, CO'\n")

    update_location("Seattle, WA", config_path=config_file)
    update_location("Chicago, IL", config_path=config_file)

    result = yaml.safe_load(config_file.read_text())
    assert result["search"]["location"] == "Chicago, IL"
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_web_config_writer.py -v
```

Expected: `FAILED` — `ModuleNotFoundError: No module named 'web'`

- [ ] **Step 3: Create `web/__init__.py` and `web/config_writer.py`**

Create `web/__init__.py` (empty file):

```python
```

Create `web/config_writer.py`:

```python
from pathlib import Path

import yaml

_DEFAULT_CONFIG = Path(__file__).parent.parent / "config" / "search.yaml"


def update_location(location: str, config_path: Path = _DEFAULT_CONFIG) -> None:
    data = yaml.safe_load(config_path.read_text())
    data["search"]["location"] = location
    config_path.write_text(yaml.dump(data, default_flow_style=False))
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/unit/test_web_config_writer.py -v
```

Expected: both tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add web/__init__.py web/config_writer.py tests/unit/test_web_config_writer.py
git commit -m "feat: add web/config_writer to patch search location in YAML"
```

---

## Task 4: Create `web/results.py`

**Files:**
- Create: `web/results.py`
- Create: `tests/unit/test_web_results.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/unit/test_web_results.py`:

```python
import pytest
from web.results import parse_jobs, parse_contacts


SAMPLE_OUTPUT = {
    "type": "a2ui",
    "version": "0.8",
    "job_table": {
        "columns": ["#", "role", "company", "score", "apply"],
        "rows": [
            {"role": "Data Engineer", "company": "Acme", "score": 8.5, "apply": "https://acme.com/jobs/1"},
            {"role": "ML Engineer", "company": "Globex", "score": 7.2, "apply": "https://globex.com/jobs/2"},
        ],
    },
    "contact_table": {
        "columns": ["#", "name", "title", "category", "relevance_score", "linkedin_url", "message"],
        "rows": [
            {
                "name": "Jane Smith",
                "title": "Sr. Recruiter",
                "category": "recruiter",
                "relevance_score": 9.0,
                "linkedin_url": "https://linkedin.com/in/janesmith",
                "message": "Hi Jane, I noticed your work at Acme…",
            },
            {
                "name": "Bob Jones",
                "title": "Data Engineer",
                "category": "peer",
                "relevance_score": 7.5,
                "linkedin_url": "",
                "message": "",
            },
        ],
    },
    "priority_summary": [],
}


def test_parse_jobs_returns_rows():
    jobs = parse_jobs(SAMPLE_OUTPUT)
    assert len(jobs) == 2
    assert jobs[0]["role"] == "Data Engineer"
    assert jobs[1]["company"] == "Globex"


def test_parse_jobs_empty_when_missing():
    jobs = parse_jobs({})
    assert jobs == []


def test_parse_contacts_returns_rows():
    contacts = parse_contacts(SAMPLE_OUTPUT)
    assert len(contacts) == 2
    assert contacts[0]["name"] == "Jane Smith"
    assert contacts[0]["linkedin_url"] == "https://linkedin.com/in/janesmith"


def test_parse_contacts_message_embedded_in_contact():
    contacts = parse_contacts(SAMPLE_OUTPUT)
    assert contacts[0]["message"] == "Hi Jane, I noticed your work at Acme…"
    assert contacts[1]["message"] == ""


def test_parse_contacts_empty_when_missing():
    contacts = parse_contacts({})
    assert contacts == []
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/unit/test_web_results.py -v
```

Expected: `FAILED` — `ImportError: cannot import name 'parse_jobs'`

- [ ] **Step 3: Create `web/results.py`**

```python
def parse_jobs(data: dict) -> list[dict]:
    return data.get("job_table", {}).get("rows", [])


def parse_contacts(data: dict) -> list[dict]:
    return data.get("contact_table", {}).get("rows", [])
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/unit/test_web_results.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 5: Run full unit suite to check for regressions**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add web/results.py tests/unit/test_web_results.py
git commit -m "feat: add web/results to parse output.json into job and contact lists"
```

---

## Task 5: Create `web/app.py`

**Files:**
- Create: `web/app.py`

No unit tests — Streamlit's rendering cannot be unit tested. The helper functions (`config_writer`, `results`) are already tested. Manual verification is the test here (see Step 2).

- [ ] **Step 1: Create `web/app.py`**

```python
import json
import sys
import tempfile
from pathlib import Path
import subprocess

import streamlit as st

from web.config_writer import update_location
from web.results import parse_contacts, parse_jobs

OUTPUT_PATH = Path(__file__).parent.parent / "output" / "output.json"
APP_ROOT = Path(__file__).parent.parent


def _run_pipeline(cv_path: str, location: str, keywords: list[str]) -> int:
    update_location(location)
    cmd = [sys.executable, "cli.py", "full", "--cv", cv_path, "--no-ui"]
    if keywords:
        cmd += ["--keywords"] + keywords
    result = subprocess.run(cmd, cwd=APP_ROOT)
    return result.returncode


def _render_jobs(jobs: list[dict]) -> None:
    if not jobs:
        st.info("No jobs found.")
        return
    rows = [
        {"Title": j.get("role", ""), "Company": j.get("company", ""), "Score": j.get("score", ""), "Apply": j.get("apply", "")}
        for j in jobs
    ]
    st.dataframe(rows, use_container_width=True)


def _render_contacts(contacts: list[dict]) -> None:
    if not contacts:
        st.info("No contacts found.")
        return
    for c in contacts:
        linkedin = c.get("linkedin_url", "")
        link = f"[Profile]({linkedin})" if linkedin else "—"
        st.markdown(
            f"**{c.get('name', '')}** · {c.get('title', '')} · {c.get('category', '')} "
            f"· Score: {c.get('relevance_score', '')} · {link}"
        )


def _render_messages(contacts: list[dict]) -> None:
    has_messages = any(c.get("message") for c in contacts)
    if not has_messages:
        st.info("No outreach messages generated.")
        return
    for c in contacts:
        msg = c.get("message", "")
        if msg:
            st.markdown(f"**{c.get('name', '')}**")
            st.text_area(
                label="",
                value=msg,
                height=100,
                disabled=True,
                key=f"msg_{c.get('name', '')}_{c.get('linkedin_url', '')}",
            )


def main() -> None:
    st.title("Job Search Agent")
    st.markdown(
        "Upload your resume, tell us what you're looking for, "
        "and we'll find matching jobs and contacts for you."
    )

    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    location = st.text_input("Where are you looking?", value="Denver, CO")
    keywords_raw = st.text_input(
        "What kind of jobs? (comma-separated)",
        value="",
        placeholder="e.g. Python, Data Engineering",
    )

    if st.button("Find My Jobs", disabled=uploaded_file is None):
        keywords = [k.strip() for k in keywords_raw.split(",") if k.strip()]

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(uploaded_file.getbuffer())
            cv_path = tmp.name

        with st.spinner("Searching for jobs… this takes 2–3 minutes"):
            returncode = _run_pipeline(cv_path, location, keywords)

        if returncode != 0:
            st.error("Something went wrong. Check that your API keys are valid and try again.")
            return

        if not OUTPUT_PATH.exists():
            st.warning("No results found. Try different keywords or a broader location.")
            return

        try:
            data = json.loads(OUTPUT_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            st.warning("No results found. Try different keywords or a broader location.")
            return

        jobs = parse_jobs(data)
        contacts = parse_contacts(data)
        message_count = sum(1 for c in contacts if c.get("message"))

        with st.expander(f"Top Jobs ({len(jobs)})", expanded=True):
            _render_jobs(jobs)

        with st.expander(f"Contacts ({len(contacts)})", expanded=True):
            _render_contacts(contacts)

        with st.expander(f"Outreach Messages ({message_count})", expanded=True):
            _render_messages(contacts)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-test the UI locally (without Docker)**

If `streamlit` is installed locally (`pip install streamlit`), run:

```bash
streamlit run web/app.py
```

Open `http://localhost:8501`. Verify:
- The form renders (title, file uploader, two text inputs, button)
- Button is disabled until a PDF is uploaded
- After uploading a PDF, button becomes clickable

You do NOT need to run the full pipeline here — just confirm the UI loads without errors. `Ctrl+C` to stop.

- [ ] **Step 3: Commit**

```bash
git add web/app.py
git commit -m "feat: add Streamlit web UI for resume upload and pipeline trigger"
```

---

## Task 6: Update `docker-compose.yml`

**Files:**
- Modify: `docker-compose.yml`

- [ ] **Step 1: Add the `web` service**

Replace the contents of `docker-compose.yml` with:

```yaml
services:
  db:
    image: postgres:16-alpine
    env_file: .env
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 5s
      timeout: 5s
      retries: 5

  app:
    build: .
    env_file: .env
    environment:
      - TERM=xterm-256color
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ${RESUME_DIR}:/data
      - ./config:/app/config
      - ./output:/app/output
    stdin_open: true
    tty: true
    command: ["tail", "-f", "/dev/null"]

  web:
    build: .
    env_file: .env
    ports:
      - "8501:8501"
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - ./config:/app/config
      - ./output:/app/output
    command: ["streamlit", "run", "web/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

volumes:
  pgdata:
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml
git commit -m "feat: add web service to docker-compose for Streamlit UI"
```

---

## Task 7: Allow `.env` to be committed and pre-fill it

**Files:**
- Modify: `.gitignore`
- Modify: `.env`

> **Note:** Committing API keys is intentional here — this repo is shared privately with one friend. Do not push to a public GitHub repo with real keys.

- [ ] **Step 1: Remove `.env` from `.gitignore`**

Open `.gitignore` and delete the line that reads:

```
.env
```

Leave everything else unchanged.

- [ ] **Step 2: Update `.env` for Docker**

Open `.env` and set it to the following, filling in your real keys:

```
# --- API Keys ---
ANTHROPIC_API_KEY=<your_real_anthropic_key>
APIFY_API_TOKEN=<your_real_apify_token>
VIBE_API_KEY=<your_real_vibe_key>

# --- Database ---
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=job_search
POSTGRES_USER=jobsearch
POSTGRES_PASSWORD=jobsearch123

# --- Docker volume mount ---
# Not needed for web UI — resume is uploaded via browser
RESUME_DIR=/tmp
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore .env
git commit -m "chore: commit pre-filled .env for friend distribution (private repo only)"
```

---

## Task 8: Update README quickstart

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Prepend a new "Quickstart (Web UI)" section**

Add the following section to `README.md` immediately after the `## What It Does` section and before `## Quickstart (Docker — recommended)`:

```markdown
## Quickstart (Web UI — easiest)

No terminal knowledge required after the one-time setup.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

### 1. Download the repo

Click **Code → Download ZIP** on GitHub. Extract the folder anywhere.

### 2. Start the app (one time)

Open a terminal, navigate to the extracted folder, and run:

```bash
docker compose up --build -d
```

This takes a few minutes the first time. You only need to do it once.

### 3. Open the browser

Go to **http://localhost:8501**

### 4. Run your search

1. Upload your resume PDF
2. Enter your city (e.g. `Denver, CO`)
3. Enter job types (e.g. `Python, Data Engineering`)
4. Click **Find My Jobs**

Results appear in 2–3 minutes.

### Stop

```bash
docker compose down
```
```

- [ ] **Step 2: Run full unit suite one final time**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add Web UI quickstart section for non-technical users"
```
