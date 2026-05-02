# Job Search Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular Python job search pipeline that takes user input from the CLI, finds matching Denver-area jobs via Google and LinkedIn, scores them against a parsed resume, discovers and ranks contacts at top companies, generates personalized outreach messages, persists everything to PostgreSQL, and renders output as A2UI JSON.

**Architecture:** Linear async pipeline orchestrated by a central `Orchestrator` class. Each stage is an independent, injectable module communicating through Pydantic models — no raw dicts cross module boundaries. Google and LinkedIn searches run in parallel via `asyncio.gather`. Hydra manages all config; no hardcoded values anywhere.

**Tech Stack:** Python 3.11+, Pydantic v2, asyncpg, Hydra-core, pymupdf, anthropic SDK, apify-client, pytest + pytest-asyncio + pytest-cov

---

## Workflow

This plan follows the user's preferred TDD workflow:
1. **Tasks 1–2:** Scaffold the project and write ALL unit tests up front
2. **Tasks 3–21:** Implement each module guided by its failing tests (Socratic TDD coaching)

---

## File Map

| File | Created/Modified | Role |
|---|---|---|
| `requirements.txt` | Create | All dependencies |
| `.env.example` | Create | API key placeholders |
| `config/api_keys.yaml` | Create | Anthropic, Apify, Vibe, Postgres keys |
| `config/database.yaml` | Create | asyncpg pool settings |
| `config/logging.yaml` | Create | Log level, handlers |
| `config/scoring.yaml` | Create | Score thresholds, top-N caps |
| `config/search.yaml` | Create | Location, keywords, remote/onsite |
| `config/config.yaml` | Create | Hydra root config (composes all above) |
| `db/models/resume.py` | Create | `ResumeProfile` Pydantic model |
| `db/models/job.py` | Create | `Job` Pydantic model |
| `db/models/contact.py` | Create | `Contact` Pydantic model |
| `db/models/message.py` | Create | `Message` Pydantic model |
| `pipeline/state.py` | Create | `PipelineState` enum + `PipelineContext` dataclass |
| `utils/logger.py` | Create | `get_logger(name)` factory |
| `llm/protocol.py` | Create | `LLMClient` Protocol |
| `llm/claude.py` | Create | Claude implementation |
| `cv/loader.py` | Create | pymupdf PDF → raw text |
| `cv/parser.py` | Create | LLM prompt → `ResumeProfile` |
| `search/filters.py` | Create | `SearchFilters` Pydantic model |
| `search/google.py` | Create | Claude web search → `list[Job]` |
| `search/linkedin.py` | Create | Apify scraper → `list[Job]` |
| `pipeline/combiner.py` | Create | Merge + deduplicate jobs |
| `scoring/job_scorer.py` | Create | Score jobs 0–10 vs `ResumeProfile` |
| `scoring/contact_scorer.py` | Create | Score contacts 0–10 with veteran boost |
| `contacts/finder.py` | Create | Apify + Vibe Prospecting → 4-category contacts |
| `messaging/generator.py` | Create | Personalized LinkedIn messages |
| `db/connection.py` | Create | asyncpg pool setup |
| `db/repositories/job_repo.py` | Create | `JobRepository` CRUD |
| `db/repositories/contact_repo.py` | Create | `ContactRepository` CRUD |
| `ui/renderer.py` | Create | A2UI JSON output |
| `pipeline/orchestrator.py` | Create | Pipeline stage coordinator |
| `cli.py` | Create | CLI entry point (search/full/contacts-only) |
| `scheduler.py` | Create | Cron wrapper around orchestrator |
| `tests/unit/test_models.py` | Create | All Pydantic model tests |
| `tests/unit/test_state.py` | Create | State enum + context tests |
| `tests/unit/test_logger.py` | Create | Logger factory tests |
| `tests/unit/test_llm.py` | Create | LLMClient protocol + Claude client tests |
| `tests/unit/test_cv_loader.py` | Create | CVLoader tests |
| `tests/unit/test_cv_parser.py` | Create | CVParser tests |
| `tests/unit/test_google_search.py` | Create | GoogleJobSearcher tests |
| `tests/unit/test_linkedin_search.py` | Create | LinkedInJobSearcher tests |
| `tests/unit/test_combiner.py` | Create | Combiner tests |
| `tests/unit/test_job_scorer.py` | Create | JobScorer tests |
| `tests/unit/test_contact_scorer.py` | Create | ContactScorer tests |
| `tests/unit/test_contact_finder.py` | Create | ContactFinder tests |
| `tests/unit/test_message_generator.py` | Create | MessageGenerator tests |
| `tests/unit/test_repositories.py` | Create | JobRepository + ContactRepository tests |
| `tests/unit/test_ui_renderer.py` | Create | UIRenderer tests |
| `tests/unit/test_orchestrator.py` | Create | Orchestrator tests |
| `tests/integration/test_pipeline.py` | Create | Real-API integration tests (run manually) |

---

## Task 1: Project Scaffolding

**Files:**
- Create: all package folders with `__init__.py`
- Create: `requirements.txt`, `.env.example`, `conftest.py`

- [x] **Step 1: Create all package directories**

```bash
mkdir -p config cv db/models db/repositories llm pipeline \
         scoring contacts messaging ui utils search \
         tests/unit tests/integration
```

- [x] **Step 2: Create `__init__.py` for every package**

```bash
touch cv/__init__.py db/__init__.py db/models/__init__.py \
      db/repositories/__init__.py llm/__init__.py \
      pipeline/__init__.py scoring/__init__.py \
      contacts/__init__.py messaging/__init__.py \
      ui/__init__.py utils/__init__.py search/__init__.py \
      tests/__init__.py tests/unit/__init__.py \
      tests/integration/__init__.py
```

- [x] **Step 3: Create `requirements.txt`**

```
anthropic>=0.40.0
pydantic>=2.0.0
asyncpg>=0.29.0
hydra-core>=1.3.0
omegaconf>=2.3.0
pymupdf>=1.24.0
apify-client>=1.6.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
python-dotenv>=1.0.0
```

- [x] **Step 3b: Create `pyproject.toml` (pytest-asyncio config)**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [x] **Step 4: Create `.env.example`**

```
ANTHROPIC_API_KEY=your_anthropic_key_here
APIFY_API_TOKEN=your_apify_token_here
VIBE_API_KEY=your_vibe_prospecting_key_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=job_search
POSTGRES_USER=your_pg_user
POSTGRES_PASSWORD=your_pg_password
```

- [x] **Step 5: Create `conftest.py` at project root**

```python
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from uuid import uuid4
from db.models.resume import ResumeProfile
from db.models.job import Job
from db.models.contact import Contact


@pytest.fixture
def sample_resume():
    return ResumeProfile(
        skills=["Python", "SQL", "Machine Learning"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Experienced software engineer",
    )


@pytest.fixture
def sample_veteran_resume():
    return ResumeProfile(
        skills=["Leadership", "Python", "Data Analysis"],
        experience_years=8,
        seniority="senior",
        location="Denver, CO",
        is_veteran=True,
        summary="Army veteran turned software engineer",
    )


@pytest.fixture
def sample_job():
    return Job(
        title="Senior Software Engineer",
        company="Acme Corp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com/apply",
        raw_description="We need a senior Python engineer...",
    )


@pytest.fixture
def sample_contact():
    return Contact(
        name="Jane Smith",
        title="Engineering Manager",
        company="Acme Corp",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/janesmith",
        relevance_score=8.5,
        is_veteran=False,
        notes="Manages the platform team",
    )


@pytest.fixture
def fake_llm():
    mock = MagicMock()
    mock.complete = MagicMock(return_value='{"result": "ok"}')
    return mock
```

- [x] **Step 6: Create empty placeholder files for all source modules**

```bash
touch cv/loader.py cv/parser.py \
      db/connection.py \
      db/models/resume.py db/models/job.py \
      db/models/contact.py db/models/message.py \
      db/repositories/job_repo.py db/repositories/contact_repo.py \
      llm/protocol.py llm/claude.py \
      pipeline/state.py pipeline/combiner.py pipeline/orchestrator.py \
      scoring/job_scorer.py scoring/contact_scorer.py \
      contacts/finder.py messaging/generator.py \
      search/filters.py search/google.py search/linkedin.py \
      ui/renderer.py utils/logger.py \
      cli.py scheduler.py
```

- [x] **Step 7: Create empty test files**

```bash
touch tests/unit/test_models.py tests/unit/test_state.py \
      tests/unit/test_logger.py tests/unit/test_llm.py \
      tests/unit/test_cv_loader.py tests/unit/test_cv_parser.py \
      tests/unit/test_google_search.py tests/unit/test_linkedin_search.py \
      tests/unit/test_combiner.py tests/unit/test_job_scorer.py \
      tests/unit/test_contact_scorer.py tests/unit/test_contact_finder.py \
      tests/unit/test_message_generator.py tests/unit/test_repositories.py \
      tests/unit/test_ui_renderer.py tests/unit/test_orchestrator.py \
      tests/integration/test_pipeline.py
```

- [x] **Step 8: Install dependencies**

```bash
pip install -r requirements.txt
```

- [x] **Step 9: Commit scaffolding**

```bash
git add .
git commit -m "chore: project scaffolding — packages, dependencies, conftest"
```

---

## Task 2: Hydra Config Files

**Files:**
- Create: `config/config.yaml`, `config/api_keys.yaml`, `config/database.yaml`, `config/logging.yaml`, `config/scoring.yaml`, `config/search.yaml`

- [x] **Step 1: Create `config/config.yaml` (Hydra root — composes all sub-configs)**

```yaml
defaults:
  - api_keys
  - database
  - logging
  - scoring
  - search
  - _self_
```

- [x] **Step 2: Create `config/api_keys.yaml`**

```yaml
anthropic_api_key: ${oc.env:ANTHROPIC_API_KEY}
apify_api_token: ${oc.env:APIFY_API_TOKEN}
vibe_api_key: ${oc.env:VIBE_API_KEY}
```

- [x] **Step 3: Create `config/database.yaml`**

```yaml
host: ${oc.env:POSTGRES_HOST,localhost}
port: ${oc.env:POSTGRES_PORT,5432}
db: ${oc.env:POSTGRES_DB,job_search}
user: ${oc.env:POSTGRES_USER}
password: ${oc.env:POSTGRES_PASSWORD}
min_pool_size: 2
max_pool_size: 10
```

- [x] **Step 4: Create `config/logging.yaml`**

```yaml
level: INFO
format: "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
file:
  path: logs/job_search.log
  max_bytes: 10485760
  backup_count: 3
```

- [x] **Step 5: Create `config/scoring.yaml`**

```yaml
job_score_threshold: 7.0
contact_score_threshold: 7.0
top_n_jobs: 10
max_contacts_per_category: 8
veteran_score_boost: 1.5
```

- [x] **Step 6: Create `config/search.yaml`**

```yaml
location: "Denver, CO"
keywords: []
remote: true
onsite: true
job_type: "full-time"
time_window_hours: 24
```

- [x] **Step 7: Commit configs**

```bash
git add config/
git commit -m "chore: add Hydra configuration files"
```

---

## Task 3: Write All Unit Tests

**Files:**
- Write: all files in `tests/unit/`

> These tests are written BEFORE any implementation. They define the contract for each module. All tests will FAIL until the corresponding module is implemented.

- [x] **Step 1: Write `tests/unit/test_models.py`**

```python
import pytest
from uuid import UUID
from datetime import datetime, timezone
from pydantic import ValidationError
from db.models.resume import ResumeProfile
from db.models.job import Job
from db.models.contact import Contact
from db.models.message import Message


# --- ResumeProfile ---

def test_resume_profile_stores_fields():
    profile = ResumeProfile(
        skills=["Python", "SQL"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Experienced engineer",
    )
    assert profile.skills == ["Python", "SQL"]
    assert profile.experience_years == 5
    assert profile.is_veteran is False


def test_resume_profile_is_veteran_defaults_false():
    profile = ResumeProfile(
        skills=[], experience_years=0,
        seniority="junior", location="Denver, CO", summary="",
    )
    assert profile.is_veteran is False


def test_resume_profile_rejects_wrong_type():
    with pytest.raises(ValidationError):
        ResumeProfile(
            skills="not a list",
            experience_years="five",
            seniority="senior",
            location="Denver, CO",
            summary="",
        )


# --- Job ---

def test_job_auto_generates_uuid():
    job = Job(
        title="Engineer",
        company="Acme",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
    )
    assert isinstance(job.id, UUID)


def test_job_fit_score_defaults_none():
    job = Job(
        title="Engineer",
        company="Acme",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
    )
    assert job.fit_score is None


def test_job_source_accepts_google_and_linkedin():
    for source in ("google", "linkedin"):
        job = Job(
            title="Engineer",
            company="Acme",
            posted_at=datetime.now(timezone.utc),
            source=source,
            apply_url="https://example.com",
            raw_description="desc",
        )
        assert job.source == source


# --- Contact ---

def test_contact_auto_generates_uuid():
    contact = Contact(
        name="Jane",
        title="Manager",
        company="Acme",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.0,
        is_veteran=False,
        notes="Short note",
    )
    assert isinstance(contact.id, UUID)


def test_contact_email_defaults_none():
    contact = Contact(
        name="Jane",
        title="Manager",
        company="Acme",
        category="recruiter",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=7.5,
        is_veteran=False,
        notes="",
    )
    assert contact.email is None


def test_contact_accepts_all_four_categories():
    for category in ("veteran", "hiring_manager", "recruiter", "peer"):
        c = Contact(
            name="X", title="Y", company="Z",
            category=category,
            linkedin_url="https://linkedin.com/in/x",
            relevance_score=8.0,
            is_veteran=(category == "veteran"),
            notes="",
        )
        assert c.category == category


# --- Message ---

def test_message_calculates_character_count():
    from uuid import uuid4
    msg = Message(
        contact_id=uuid4(),
        job_id=uuid4(),
        message_text="Hello, this is a test message.",
    )
    assert msg.character_count == len("Hello, this is a test message.")


def test_message_rejects_text_over_300_chars():
    from uuid import uuid4
    with pytest.raises(ValidationError):
        Message(
            contact_id=uuid4(),
            job_id=uuid4(),
            message_text="x" * 301,
        )
```

- [x] **Step 2: Write `tests/unit/test_state.py`**

```python
import pytest
from pipeline.state import PipelineState, PipelineContext


def test_pipeline_state_has_expected_values():
    assert PipelineState.IDLE.value == "idle"
    assert PipelineState.SEARCHING.value == "searching"
    assert PipelineState.COMPLETE.value == "complete"
    assert PipelineState.ERROR.value == "error"


def test_pipeline_context_initializes_with_empty_collections():
    ctx = PipelineContext()
    assert ctx.jobs == []
    assert ctx.contacts == []
    assert ctx.messages == []
    assert ctx.errors == []


def test_pipeline_context_default_state_is_idle():
    ctx = PipelineContext()
    assert ctx.state == PipelineState.IDLE


def test_pipeline_context_state_can_be_updated():
    ctx = PipelineContext()
    ctx.state = PipelineState.SEARCHING
    assert ctx.state == PipelineState.SEARCHING


def test_pipeline_context_errors_accumulate():
    ctx = PipelineContext()
    ctx.errors.append("something went wrong")
    assert len(ctx.errors) == 1
```

- [x] **Step 3: Write `tests/unit/test_logger.py`**

```python
import logging
from utils.logger import get_logger


def test_get_logger_returns_logger_instance():
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)


def test_get_logger_uses_provided_name():
    logger = get_logger("my.custom.name")
    assert logger.name == "my.custom.name"


def test_get_logger_different_names_return_different_loggers():
    logger_a = get_logger("module.a")
    logger_b = get_logger("module.b")
    assert logger_a is not logger_b
```

- [x] **Step 4: Write `tests/unit/test_llm.py`**

```python
import pytest
from unittest.mock import MagicMock, patch
from llm.protocol import LLMClient
from llm.claude import ClaudeClient


def test_llm_client_is_a_protocol():
    from typing import runtime_checkable, Protocol
    assert issubclass(LLMClient, Protocol)


def test_claude_client_implements_llm_client_protocol():
    with patch("llm.claude.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = MagicMock()
        client = ClaudeClient(api_key="test-key")
        assert isinstance(client, LLMClient)


def test_claude_client_complete_calls_sdk_messages_create():
    with patch("llm.claude.anthropic") as mock_anthropic:
        mock_messages = MagicMock()
        mock_messages.create.return_value.content = [MagicMock(text="response text")]
        mock_anthropic.Anthropic.return_value.messages = mock_messages

        client = ClaudeClient(api_key="test-key")
        result = client.complete(system="You are helpful.", user="Hello")

        mock_messages.create.assert_called_once()
        assert result == "response text"


def test_claude_client_passes_system_and_user_to_sdk():
    with patch("llm.claude.anthropic") as mock_anthropic:
        mock_messages = MagicMock()
        mock_messages.create.return_value.content = [MagicMock(text="ok")]
        mock_anthropic.Anthropic.return_value.messages = mock_messages

        client = ClaudeClient(api_key="key")
        client.complete(system="sys prompt", user="user msg")

        call_kwargs = mock_messages.create.call_args.kwargs
        assert call_kwargs["system"] == "sys prompt"
        assert call_kwargs["messages"][0]["content"] == "user msg"
```

- [x] **Step 5: Write `tests/unit/test_cv_loader.py`**

```python
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from cv.loader import CVLoader


def test_cv_loader_returns_text_from_pdf():
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Page one text"
    mock_doc = MagicMock()
    mock_doc.__iter__ = MagicMock(return_value=iter([mock_page]))

    with patch("cv.loader.fitz.open", return_value=mock_doc):
        loader = CVLoader()
        result = loader.load("resume.pdf")

    assert "Page one text" in result


def test_cv_loader_concatenates_multiple_pages():
    pages = [MagicMock(), MagicMock()]
    pages[0].get_text.return_value = "Page one"
    pages[1].get_text.return_value = "Page two"
    mock_doc = MagicMock()
    mock_doc.__iter__ = MagicMock(return_value=iter(pages))

    with patch("cv.loader.fitz.open", return_value=mock_doc):
        loader = CVLoader()
        result = loader.load("resume.pdf")

    assert "Page one" in result
    assert "Page two" in result


def test_cv_loader_raises_on_missing_file():
    with patch("cv.loader.fitz.open", side_effect=FileNotFoundError):
        loader = CVLoader()
        with pytest.raises(FileNotFoundError):
            loader.load("missing.pdf")
```

- [x] **Step 6: Write `tests/unit/test_cv_parser.py`**

```python
import json
import pytest
from unittest.mock import MagicMock
from cv.parser import CVParser
from db.models.resume import ResumeProfile


def _make_llm(response_dict: dict) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = json.dumps(response_dict)
    return mock


def test_cv_parser_returns_resume_profile():
    llm = _make_llm({
        "skills": ["Python"],
        "experience_years": 3,
        "seniority": "mid",
        "location": "Denver, CO",
        "is_veteran": False,
        "summary": "A developer",
    })
    parser = CVParser(llm=llm)
    result = parser.parse("raw resume text")
    assert isinstance(result, ResumeProfile)


def test_cv_parser_calls_llm_with_resume_text():
    llm = _make_llm({
        "skills": [], "experience_years": 0,
        "seniority": "junior", "location": "Denver",
        "is_veteran": False, "summary": "",
    })
    parser = CVParser(llm=llm)
    parser.parse("raw resume text here")
    llm.complete.assert_called_once()
    call_kwargs = llm.complete.call_args.kwargs
    assert "raw resume text here" in call_kwargs["user"]


def test_cv_parser_infers_is_veteran_true_from_llm():
    llm = _make_llm({
        "skills": ["Leadership"],
        "experience_years": 8,
        "seniority": "senior",
        "location": "Denver, CO",
        "is_veteran": True,
        "summary": "Army veteran",
    })
    parser = CVParser(llm=llm)
    result = parser.parse("U.S. Army, Staff Sergeant, 2012-2020")
    assert result.is_veteran is True


def test_cv_parser_infers_is_veteran_false_when_no_signals():
    llm = _make_llm({
        "skills": ["Python"],
        "experience_years": 3,
        "seniority": "mid",
        "location": "Denver, CO",
        "is_veteran": False,
        "summary": "Software engineer",
    })
    parser = CVParser(llm=llm)
    result = parser.parse("Worked at Google for 3 years")
    assert result.is_veteran is False


def test_cv_parser_system_prompt_contains_veteran_signals():
    from cv.parser import SYSTEM_PROMPT
    assert "veteran" in SYSTEM_PROMPT.lower()
    assert "military" in SYSTEM_PROMPT.lower() or "MOS" in SYSTEM_PROMPT
```

- [x] **Step 7: Write `tests/unit/test_google_search.py`**

```python
import json
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta
from search.google import GoogleJobSearcher
from search.filters import SearchFilters
from db.models.job import Job


def _make_llm(jobs_list: list) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = json.dumps(jobs_list)
    return mock


def _recent_iso():
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def test_google_searcher_returns_list_of_jobs():
    llm = _make_llm([{
        "title": "Engineer",
        "company": "Acme",
        "posted_at": _recent_iso(),
        "apply_url": "https://example.com",
        "raw_description": "Python role",
    }])
    searcher = GoogleJobSearcher(llm=llm)
    results = searcher.search(SearchFilters(keywords=["Python"]))
    assert len(results) == 1
    assert isinstance(results[0], Job)


def test_google_searcher_sets_source_to_google():
    llm = _make_llm([{
        "title": "Engineer", "company": "Acme",
        "posted_at": _recent_iso(),
        "apply_url": "https://example.com",
        "raw_description": "desc",
    }])
    searcher = GoogleJobSearcher(llm=llm)
    results = searcher.search(SearchFilters())
    assert results[0].source == "google"


def test_google_searcher_filters_out_old_jobs():
    old_time = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    llm = _make_llm([{
        "title": "Old Job", "company": "Acme",
        "posted_at": old_time,
        "apply_url": "https://example.com",
        "raw_description": "desc",
    }])
    searcher = GoogleJobSearcher(llm=llm)
    results = searcher.search(SearchFilters(time_window_hours=24))
    assert results == []


def test_google_searcher_passes_filters_to_llm():
    llm = _make_llm([])
    searcher = GoogleJobSearcher(llm=llm)
    filters = SearchFilters(keywords=["Python", "Django"], location="Denver, CO")
    searcher.search(filters)
    llm.complete.assert_called_once()
    call_kwargs = llm.complete.call_args.kwargs
    user_payload = json.loads(call_kwargs["user"])
    assert "Python" in user_payload["keywords"]
    assert user_payload["location"] == "Denver, CO"
```

- [x] **Step 8: Write `tests/unit/test_linkedin_search.py`**

```python
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from search.linkedin import LinkedInJobSearcher
from search.filters import SearchFilters
from db.models.job import Job


def _recent_iso():
    return (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()


def test_linkedin_searcher_returns_list_of_jobs():
    mock_item = {
        "title": "Data Engineer",
        "companyName": "TechCorp",
        "postedAt": _recent_iso(),
        "jobUrl": "https://linkedin.com/jobs/123",
        "description": "Build pipelines",
    }
    with patch("search.linkedin.ApifyClient") as MockApify:
        mock_run = {"defaultDatasetId": "dataset-123"}
        MockApify.return_value.actor.return_value.call.return_value = mock_run
        MockApify.return_value.dataset.return_value.iterate_items.return_value = iter([mock_item])

        searcher = LinkedInJobSearcher(api_token="test-token")
        results = searcher.search(SearchFilters(keywords=["Python"]))

    assert len(results) == 1
    assert isinstance(results[0], Job)


def test_linkedin_searcher_sets_source_to_linkedin():
    mock_item = {
        "title": "Engineer", "companyName": "Corp",
        "postedAt": _recent_iso(),
        "jobUrl": "https://linkedin.com/jobs/1",
        "description": "desc",
    }
    with patch("search.linkedin.ApifyClient") as MockApify:
        mock_run = {"defaultDatasetId": "ds1"}
        MockApify.return_value.actor.return_value.call.return_value = mock_run
        MockApify.return_value.dataset.return_value.iterate_items.return_value = iter([mock_item])

        searcher = LinkedInJobSearcher(api_token="token")
        results = searcher.search(SearchFilters())

    assert results[0].source == "linkedin"


def test_linkedin_searcher_filters_old_jobs():
    old_item = {
        "title": "Old Job", "companyName": "OldCo",
        "postedAt": (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat(),
        "jobUrl": "https://linkedin.com/jobs/2",
        "description": "old",
    }
    with patch("search.linkedin.ApifyClient") as MockApify:
        mock_run = {"defaultDatasetId": "ds2"}
        MockApify.return_value.actor.return_value.call.return_value = mock_run
        MockApify.return_value.dataset.return_value.iterate_items.return_value = iter([old_item])

        searcher = LinkedInJobSearcher(api_token="token")
        results = searcher.search(SearchFilters(time_window_hours=24))

    assert results == []
```

- [x] **Step 9: Write `tests/unit/test_combiner.py`**

```python
import pytest
from datetime import datetime, timezone
from db.models.job import Job
from pipeline.combiner import combine_jobs


def _make_job(title, company, source="google"):
    return Job(
        title=title, company=company,
        posted_at=datetime.now(timezone.utc),
        source=source, apply_url="https://example.com",
        raw_description="desc",
    )


def test_combine_jobs_merges_two_lists():
    google_jobs = [_make_job("Engineer", "Acme", "google")]
    linkedin_jobs = [_make_job("Analyst", "BetaCo", "linkedin")]
    result = combine_jobs(google_jobs, linkedin_jobs)
    assert len(result) == 2


def test_combine_jobs_deduplicates_by_title_and_company():
    job_a = _make_job("Engineer", "Acme", "google")
    job_b = _make_job("Engineer", "Acme", "linkedin")
    result = combine_jobs([job_a], [job_b])
    assert len(result) == 1


def test_combine_jobs_keeps_google_version_on_duplicate():
    job_a = _make_job("Engineer", "Acme", "google")
    job_b = _make_job("Engineer", "Acme", "linkedin")
    result = combine_jobs([job_a], [job_b])
    assert result[0].source == "google"


def test_combine_jobs_handles_empty_lists():
    result = combine_jobs([], [])
    assert result == []


def test_combine_jobs_preserves_unique_jobs_from_both_sources():
    google_jobs = [_make_job("Engineer", "Acme"), _make_job("Analyst", "BetaCo")]
    linkedin_jobs = [_make_job("Engineer", "Acme"), _make_job("Designer", "GammaCo")]
    result = combine_jobs(google_jobs, linkedin_jobs)
    companies = {j.company for j in result}
    assert companies == {"Acme", "BetaCo", "GammaCo"}
```

- [x] **Step 10: Write `tests/unit/test_job_scorer.py`**

```python
import json
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone
from db.models.job import Job
from db.models.resume import ResumeProfile
from scoring.job_scorer import JobScorer


def _make_resume():
    return ResumeProfile(
        skills=["Python", "SQL"],
        experience_years=5,
        seniority="senior",
        location="Denver, CO",
        is_veteran=False,
        summary="Experienced engineer",
    )


def _make_job(title="Engineer", company="Acme"):
    return Job(
        title=title, company=company,
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="Python developer needed",
    )


def _make_llm(score: float) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = json.dumps({"score": score, "reason": "Good fit"})
    return mock


def test_job_scorer_sets_fit_score_on_each_job():
    llm = _make_llm(8.0)
    scorer = JobScorer(llm=llm)
    jobs = [_make_job()]
    result = scorer.score(jobs, _make_resume())
    assert result[0].fit_score == 8.0


def test_job_scorer_score_is_between_0_and_10():
    llm = _make_llm(9.5)
    scorer = JobScorer(llm=llm)
    result = scorer.score([_make_job()], _make_resume())
    assert 0.0 <= result[0].fit_score <= 10.0


def test_job_scorer_calls_llm_once_per_job():
    llm = _make_llm(7.0)
    scorer = JobScorer(llm=llm)
    jobs = [_make_job("Job A"), _make_job("Job B"), _make_job("Job C")]
    scorer.score(jobs, _make_resume())
    assert llm.complete.call_count == 3


def test_job_scorer_passes_resume_skills_to_llm():
    llm = _make_llm(7.5)
    scorer = JobScorer(llm=llm)
    resume = _make_resume()
    scorer.score([_make_job()], resume)
    call_kwargs = llm.complete.call_args.kwargs
    assert "Python" in call_kwargs["user"]


def test_job_scorer_sorts_by_score_descending():
    scores = [6.0, 9.0, 7.5]
    call_count = [0]

    def fake_complete(**kwargs):
        score = scores[call_count[0]]
        call_count[0] += 1
        return json.dumps({"score": score, "reason": ""})

    llm = MagicMock()
    llm.complete.side_effect = fake_complete
    scorer = JobScorer(llm=llm)
    result = scorer.score([_make_job("A"), _make_job("B"), _make_job("C")], _make_resume())
    assert result[0].fit_score == 9.0
    assert result[-1].fit_score == 6.0
```

- [x] **Step 11: Write `tests/unit/test_contact_scorer.py`**

```python
import pytest
from db.models.contact import Contact
from scoring.contact_scorer import ContactScorer


def _make_contact(category="hiring_manager", is_veteran=False, score=7.5):
    return Contact(
        name="Test Person",
        title="Manager",
        company="Acme",
        category=category,
        linkedin_url="https://linkedin.com/in/test",
        relevance_score=score,
        is_veteran=is_veteran,
        notes="",
    )


def test_contact_scorer_filters_below_threshold():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    contacts = [_make_contact(score=6.5), _make_contact(score=8.0)]
    result = scorer.filter_and_sort(contacts, searcher_is_veteran=False)
    assert len(result) == 1
    assert result[0].relevance_score == 8.0


def test_contact_scorer_applies_veteran_boost_when_searcher_is_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    vet_contact = _make_contact(category="veteran", is_veteran=True, score=6.0)
    result = scorer.filter_and_sort([vet_contact], searcher_is_veteran=True)
    assert len(result) == 1
    assert result[0].relevance_score == pytest.approx(7.5)


def test_contact_scorer_no_boost_when_searcher_is_not_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    vet_contact = _make_contact(category="veteran", is_veteran=True, score=6.0)
    result = scorer.filter_and_sort([vet_contact], searcher_is_veteran=False)
    assert result == []


def test_contact_scorer_sorts_veterans_first_when_searcher_is_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    peer = _make_contact(category="peer", is_veteran=False, score=9.0)
    vet = _make_contact(category="veteran", is_veteran=True, score=7.0)
    boosted_vet_score = 7.0 + 1.5
    result = scorer.filter_and_sort([peer, vet], searcher_is_veteran=True)
    assert result[0].category == "veteran"


def test_contact_scorer_standard_order_when_not_veteran():
    scorer = ContactScorer(threshold=7.0, veteran_boost=1.5)
    recruiter = _make_contact(category="recruiter", score=9.0)
    hiring_manager = _make_contact(category="hiring_manager", score=8.0)
    peer = _make_contact(category="peer", score=7.5)
    result = scorer.filter_and_sort([recruiter, peer, hiring_manager], searcher_is_veteran=False)
    assert result[0].category == "hiring_manager"
```

- [x] **Step 12: Write `tests/unit/test_contact_finder.py`**

```python
import pytest
from unittest.mock import MagicMock, patch
from contacts.finder import ContactFinder
from db.models.job import Job
from datetime import datetime, timezone


def _make_job():
    return Job(
        title="Senior Engineer",
        company="TechCorp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="Python role",
    )


def test_contact_finder_returns_contacts_for_job():
    mock_apify = MagicMock()
    mock_vibe = MagicMock()

    mock_apify.find_people.return_value = [
        {"name": "Jane", "title": "Engineering Manager", "linkedin_url": "https://linkedin.com/in/jane",
         "company": "TechCorp", "is_veteran": False, "email": None},
    ]
    mock_vibe.enrich.return_value = []

    finder = ContactFinder(apify_client=mock_apify, vibe_client=mock_vibe, max_per_category=8)
    result = finder.find(_make_job())
    assert len(result) >= 1


def test_contact_finder_only_includes_current_employees():
    mock_apify = MagicMock()
    mock_vibe = MagicMock()
    mock_apify.find_people.return_value = [
        {"name": "Bob", "title": "Former Manager", "linkedin_url": "https://linkedin.com/in/bob",
         "company": "OtherCorp", "is_veteran": False, "email": None},
    ]
    mock_vibe.enrich.return_value = []

    finder = ContactFinder(apify_client=mock_apify, vibe_client=mock_vibe, max_per_category=8)
    result = finder.find(_make_job())
    for contact in result:
        assert contact.company == "TechCorp"


def test_contact_finder_respects_max_per_category():
    mock_apify = MagicMock()
    mock_vibe = MagicMock()
    many_people = [
        {"name": f"Person {i}", "title": "Recruiter", "linkedin_url": f"https://linkedin.com/in/p{i}",
         "company": "TechCorp", "is_veteran": False, "email": None}
        for i in range(20)
    ]
    mock_apify.find_people.return_value = many_people
    mock_vibe.enrich.return_value = []

    finder = ContactFinder(apify_client=mock_apify, vibe_client=mock_vibe, max_per_category=3)
    result = finder.find(_make_job())
    recruiters = [c for c in result if c.category == "recruiter"]
    assert len(recruiters) <= 3
```

- [x] **Step 13: Write `tests/unit/test_message_generator.py`**

```python
import pytest
from unittest.mock import MagicMock
from messaging.generator import MessageGenerator
from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message
from datetime import datetime, timezone
from uuid import uuid4


def _make_job():
    return Job(
        title="Senior Engineer",
        company="TechCorp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="Looking for a Python expert with 5+ years experience",
    )


def _make_contact(category="hiring_manager"):
    return Contact(
        name="Jane Smith",
        title="Engineering Manager",
        company="TechCorp",
        category=category,
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.5,
        is_veteran=False,
        notes="Manages platform team",
    )


def _make_llm(response: str) -> MagicMock:
    mock = MagicMock()
    mock.complete.return_value = response
    return mock


def test_message_generator_returns_message_object():
    llm = _make_llm("Hi Jane, saw you're building the platform team at TechCorp.")
    gen = MessageGenerator(llm=llm)
    result = gen.generate(_make_contact(), _make_job())
    assert isinstance(result, Message)


def test_message_generator_message_under_300_chars():
    llm = _make_llm("Short message under 300 chars.")
    gen = MessageGenerator(llm=llm)
    result = gen.generate(_make_contact(), _make_job())
    assert result.character_count <= 300


def test_message_generator_links_contact_and_job_ids():
    contact = _make_contact()
    job = _make_job()
    llm = _make_llm("Hi Jane, great opportunity.")
    gen = MessageGenerator(llm=llm)
    result = gen.generate(contact, job)
    assert result.contact_id == contact.id
    assert result.job_id == job.id


def test_message_generator_peer_message_does_not_mention_job():
    llm = _make_llm("Hey, saw your work on distributed systems — fascinating!")
    gen = MessageGenerator(llm=llm)
    contact = _make_contact(category="peer")
    result = gen.generate(contact, _make_job())
    assert isinstance(result, Message)
    llm.complete.assert_called_once()
    system_prompt_used = llm.complete.call_args.kwargs["system"]
    assert "peer" in system_prompt_used.lower() or "do not mention" in system_prompt_used.lower()


def test_message_generator_uses_job_description_for_skills():
    llm = _make_llm("Hi Jane, your Python experience aligns perfectly.")
    gen = MessageGenerator(llm=llm)
    gen.generate(_make_contact(), _make_job())
    user_payload = llm.complete.call_args.kwargs["user"]
    assert "Python" in user_payload
```

- [x] **Step 14: Write `tests/unit/test_repositories.py`**

```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from db.models.job import Job
from db.models.contact import Contact
from db.repositories.job_repo import JobRepository
from db.repositories.contact_repo import ContactRepository


def _make_job():
    return Job(
        title="Engineer",
        company="Acme",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
        fit_score=8.5,
    )


def _make_contact():
    return Contact(
        name="Jane",
        title="Manager",
        company="Acme",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.0,
        is_veteran=False,
        notes="",
    )


@pytest.mark.asyncio
async def test_job_repository_save_executes_insert():
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    repo = JobRepository(pool=mock_pool)
    await repo.save(_make_job())
    mock_conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_contact_repository_save_executes_insert():
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    repo = ContactRepository(pool=mock_pool)
    await repo.save(_make_contact(), job_id=_make_job().id)
    mock_conn.execute.assert_called_once()


@pytest.mark.asyncio
async def test_job_repository_get_all_returns_list():
    mock_pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = []
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

    repo = JobRepository(pool=mock_pool)
    result = await repo.get_all()
    assert isinstance(result, list)
```

- [x] **Step 15: Write `tests/unit/test_ui_renderer.py`**

```python
import json
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from db.models.job import Job
from db.models.contact import Contact
from db.models.message import Message
from ui.renderer import UIRenderer


def _make_job(score=8.5):
    return Job(
        title="Senior Engineer",
        company="TechCorp",
        posted_at=datetime.now(timezone.utc),
        source="google",
        apply_url="https://example.com",
        raw_description="desc",
        fit_score=score,
    )


def _make_contact():
    return Contact(
        name="Jane Smith",
        title="Engineering Manager",
        company="TechCorp",
        category="hiring_manager",
        linkedin_url="https://linkedin.com/in/jane",
        relevance_score=8.5,
        is_veteran=False,
        notes="Manages platform team",
    )


def _make_message(contact_id, job_id):
    return Message(
        contact_id=contact_id,
        job_id=job_id,
        message_text="Hi Jane, saw you're hiring at TechCorp!",
    )


def test_renderer_returns_valid_json():
    renderer = UIRenderer()
    contact = _make_contact()
    job = _make_job()
    msg = _make_message(contact.id, job.id)
    output = renderer.render(jobs=[job], contacts=[contact], messages=[msg])
    parsed = json.loads(output)
    assert isinstance(parsed, dict)


def test_renderer_output_contains_job_table():
    renderer = UIRenderer()
    output = renderer.render(jobs=[_make_job()], contacts=[], messages=[])
    parsed = json.loads(output)
    assert "job_table" in parsed or any("job" in str(k).lower() for k in parsed.keys())


def test_renderer_output_contains_contact_table():
    renderer = UIRenderer()
    contact = _make_contact()
    output = renderer.render(jobs=[], contacts=[contact], messages=[])
    parsed = json.loads(output)
    assert "contact_table" in parsed or any("contact" in str(k).lower() for k in parsed.keys())


def test_renderer_job_table_has_required_columns():
    renderer = UIRenderer()
    job = _make_job()
    output = renderer.render(jobs=[job], contacts=[], messages=[])
    output_str = output.lower()
    for col in ("role", "company", "source", "score", "apply"):
        assert col in output_str


def test_renderer_output_contains_priority_summary():
    renderer = UIRenderer()
    contact = _make_contact()
    output = renderer.render(jobs=[], contacts=[contact], messages=[])
    parsed = json.loads(output)
    assert "priority_summary" in parsed


def test_renderer_priority_summary_includes_name_and_category():
    renderer = UIRenderer()
    contact = _make_contact()
    output = renderer.render(jobs=[], contacts=[contact], messages=[])
    parsed = json.loads(output)
    summary = parsed["priority_summary"]
    assert len(summary) >= 1
    assert "name" in summary[0]
    assert "category" in summary[0]
```

- [x] **Step 16: Write `tests/unit/test_orchestrator.py`**

```python
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pipeline.orchestrator import Orchestrator
from pipeline.state import PipelineState, PipelineContext
from db.models.resume import ResumeProfile
from search.filters import SearchFilters


def _make_resume():
    return ResumeProfile(
        skills=["Python"], experience_years=5,
        seniority="senior", location="Denver, CO",
        is_veteran=False, summary="Engineer",
    )


def _make_filters():
    return SearchFilters(keywords=["Python"], location="Denver, CO")


def test_orchestrator_sets_state_to_complete_on_success():
    mock_cv_loader = MagicMock()
    mock_cv_parser = MagicMock()
    mock_cv_parser.parse.return_value = _make_resume()
    mock_google = MagicMock()
    mock_google.search.return_value = []
    mock_linkedin = MagicMock()
    mock_linkedin.search.return_value = []
    mock_scorer = MagicMock()
    mock_scorer.score.return_value = []
    mock_contact_finder = MagicMock()
    mock_contact_scorer = MagicMock()
    mock_contact_scorer.filter_and_sort.return_value = []
    mock_msg_gen = MagicMock()
    mock_job_repo = AsyncMock()
    mock_contact_repo = AsyncMock()
    mock_renderer = MagicMock()
    mock_renderer.render.return_value = '{"job_table": []}'

    orch = Orchestrator(
        cv_loader=mock_cv_loader,
        cv_parser=mock_cv_parser,
        google_searcher=mock_google,
        linkedin_searcher=mock_linkedin,
        combiner=MagicMock(return_value=[]),
        job_scorer=mock_scorer,
        contact_finder=mock_contact_finder,
        contact_scorer=mock_contact_scorer,
        message_generator=mock_msg_gen,
        job_repo=mock_job_repo,
        contact_repo=mock_contact_repo,
        renderer=mock_renderer,
        job_threshold=7.0,
        contact_threshold=7.0,
        top_n=10,
    )

    import asyncio
    ctx = asyncio.run(orch.run(cv_path="resume.pdf", filters=_make_filters()))
    assert ctx.state == PipelineState.COMPLETE


def test_orchestrator_sets_error_state_on_exception(caplog):
    mock_cv_loader = MagicMock()
    mock_cv_loader.load.side_effect = FileNotFoundError("resume.pdf not found")
    mock_cv_parser = MagicMock()

    orch = Orchestrator(
        cv_loader=mock_cv_loader,
        cv_parser=mock_cv_parser,
        google_searcher=MagicMock(),
        linkedin_searcher=MagicMock(),
        combiner=MagicMock(return_value=[]),
        job_scorer=MagicMock(),
        contact_finder=MagicMock(),
        contact_scorer=MagicMock(),
        message_generator=MagicMock(),
        job_repo=AsyncMock(),
        contact_repo=AsyncMock(),
        renderer=MagicMock(),
        job_threshold=7.0,
        contact_threshold=7.0,
        top_n=10,
    )

    import asyncio
    ctx = asyncio.run(orch.run(cv_path="missing.pdf", filters=_make_filters()))
    assert ctx.state == PipelineState.ERROR
    assert len(ctx.errors) > 0
```

- [x] **Step 17: Verify all tests are collected (they will all fail — that's correct)**

```bash
pytest tests/unit/ --collect-only 2>&1 | tail -20
```

Expected: all test files listed, errors about missing implementations.

- [x] **Step 18: Commit all test files**

```bash
git add tests/
git commit -m "test: write all unit tests before implementation (TDD)"
```

---

## Task 4: Implement Pydantic Models

**Files:**
- Write: `db/models/resume.py`, `db/models/job.py`, `db/models/contact.py`, `db/models/message.py`

- [x] **Step 1: Run failing model tests**

```bash
pytest tests/unit/test_models.py -v
```
Expected: `ImportError` — models not yet implemented.

- [x] **Step 2: Implement `db/models/resume.py`**

```python
from pydantic import BaseModel


class ResumeProfile(BaseModel):
    skills: list[str]
    experience_years: int
    seniority: str
    location: str
    is_veteran: bool = False
    summary: str
```

- [x] **Step 3: Implement `db/models/job.py`**

```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime


class Job(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    company: str
    posted_at: datetime
    source: str
    apply_url: str
    raw_description: str
    fit_score: float | None = None
```

- [x] **Step 4: Implement `db/models/contact.py`**

```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class Contact(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    title: str
    company: str
    category: str
    linkedin_url: str
    email: str | None = None
    relevance_score: float
    is_veteran: bool = False
    notes: str
```

- [x] **Step 5: Implement `db/models/message.py`**

```python
from pydantic import BaseModel, Field, model_validator
from uuid import UUID


class Message(BaseModel):
    contact_id: UUID
    job_id: UUID
    message_text: str
    character_count: int = 0

    @model_validator(mode="after")
    def check_length_and_set_count(self):
        if len(self.message_text) > 300:
            raise ValueError("message_text must be 300 characters or fewer")
        self.character_count = len(self.message_text)
        return self
```

- [x] **Step 6: Run tests — all must pass**

```bash
pytest tests/unit/test_models.py -v
```
Expected: all green.

- [x] **Step 7: Commit**

```bash
git add db/models/
git commit -m "feat: implement Pydantic models — Job, Contact, Message, ResumeProfile"
```

---

## Task 5: Implement Pipeline State

**Files:**
- Write: `pipeline/state.py`

- [x] **Step 1: Run failing state tests**

```bash
pytest tests/unit/test_state.py -v
```
Expected: `ImportError`.

- [x] **Step 2: Implement `pipeline/state.py`**

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class PipelineState(Enum):
    IDLE = "idle"
    LOADING_CV = "loading_cv"
    SEARCHING = "searching"
    SCORING_JOBS = "scoring_jobs"
    FINDING_CONTACTS = "finding_contacts"
    SCORING_CONTACTS = "scoring_contacts"
    GENERATING_MESSAGES = "generating_messages"
    SAVING = "saving"
    RENDERING = "rendering"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class PipelineContext:
    resume: Any = None        # ResumeProfile at runtime
    filters: Any = None       # SearchFilters at runtime
    jobs: list = field(default_factory=list)
    contacts: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    state: PipelineState = PipelineState.IDLE
    errors: list[str] = field(default_factory=list)
```

> Note: `Any` types avoid a circular import — `SearchFilters` is implemented after `state.py`. The orchestrator enforces the real types at runtime.

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_state.py -v
```

- [x] **Step 4: Commit**

```bash
git add pipeline/state.py search/filters.py
git commit -m "feat: implement PipelineState enum and PipelineContext"
```

---

## Task 6: Implement Logger

**Files:**
- Write: `utils/logger.py`

- [x] **Step 1: Run failing logger tests**

```bash
pytest tests/unit/test_logger.py -v
```

- [x] **Step 2: Implement `utils/logger.py`**

```python
import logging


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_logger.py -v
```

- [x] **Step 4: Commit**

```bash
git add utils/logger.py
git commit -m "feat: implement get_logger factory"
```

---

## Task 7: Implement LLM Protocol + Claude Client

**Files:**
- Write: `llm/protocol.py`, `llm/claude.py`

- [x] **Step 1: Run failing LLM tests**

```bash
pytest tests/unit/test_llm.py -v
```

- [x] **Step 2: Implement `llm/protocol.py`**

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClient(Protocol):
    def complete(self, *, system: str, user: str) -> str:
        ...
```

- [x] **Step 3: Implement `llm/claude.py`**

```python
import anthropic
from llm.protocol import LLMClient


class ClaudeClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, *, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text
```

- [x] **Step 4: Run tests — all must pass**

```bash
pytest tests/unit/test_llm.py -v
```

- [x] **Step 5: Commit**

```bash
git add llm/
git commit -m "feat: implement LLMClient protocol and ClaudeClient"
```

---

## Task 8: Implement Search Filters

**Files:**
- Write: `search/filters.py`

- [x] **Step 1: Implement `search/filters.py`**

```python
from pydantic import BaseModel


class SearchFilters(BaseModel):
    keywords: list[str] = []
    location: str = "Denver, CO"
    remote: bool = True
    onsite: bool = True
    job_type: str = "full-time"
    time_window_hours: int = 24
```

- [x] **Step 2: Verify state tests still pass (SearchFilters is imported there)**

```bash
pytest tests/unit/test_state.py tests/unit/test_models.py -v
```

- [x] **Step 3: Commit**

```bash
git add search/filters.py
git commit -m "feat: implement SearchFilters model"
```

---

## Task 9: Implement CV Loader

**Files:**
- Write: `cv/loader.py`

- [x] **Step 1: Run failing CV loader tests**

```bash
pytest tests/unit/test_cv_loader.py -v
```

- [x] **Step 2: Implement `cv/loader.py`**

```python
import fitz
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class CVLoader:
    def load(self, path: str | Path) -> str:
        logger.info(f"Loading CV from {path}")
        doc = fitz.open(str(path))
        return "\n".join(page.get_text() for page in doc)
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_cv_loader.py -v
```

- [x] **Step 4: Commit**

```bash
git add cv/loader.py
git commit -m "feat: implement CVLoader with pymupdf"
```

---

## Task 10: Implement CV Parser

**Files:**
- Write: `cv/parser.py`

- [x] **Step 1: Run failing CV parser tests**

```bash
pytest tests/unit/test_cv_parser.py -v
```

- [x] **Step 2: Implement `cv/parser.py`**

```python
import json
from llm.protocol import LLMClient
from db.models.resume import ResumeProfile
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a resume parser. Extract structured information from the resume text.

Return a JSON object with exactly these fields:
- skills: list of strings (technical and professional skills)
- experience_years: integer (total years of professional experience)
- seniority: one of "junior", "mid", "senior", "lead", "principal", "director", "executive"
- location: string (primary location)
- is_veteran: boolean — true if the resume contains ANY of these signals:
    * Military branch mention (Army, Navy, Marines, Air Force, Coast Guard, Space Force)
    * Military rank or title (Sergeant, Captain, Staff Sergeant, Lieutenant, etc.)
    * MOS or AFSC codes
    * Deployment language
    * Transition language: "separated", "ETS", "honorable discharge"
    * Military education: ROTC, service academies (West Point, Annapolis, etc.)
    * Veteran service organizations
  Set to false if none of these signals are present.
- summary: string (one paragraph professional summary)

Return ONLY valid JSON. No markdown, no explanation."""


class CVParser:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def parse(self, raw_text: str) -> ResumeProfile:
        logger.info("Parsing CV with LLM")
        response = self._llm.complete(system=SYSTEM_PROMPT, user=raw_text)
        data = json.loads(response)
        return ResumeProfile(**data)
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_cv_parser.py -v
```

- [x] **Step 4: Commit**

```bash
git add cv/parser.py
git commit -m "feat: implement CVParser with veteran inference prompt"
```

---

## Task 11: Implement Google Job Searcher

**Files:**
- Write: `search/google.py`

- [x] **Step 1: Run failing Google search tests**

```bash
pytest tests/unit/test_google_search.py -v
```

- [x] **Step 2: Implement `search/google.py`**

```python
import json
from datetime import datetime, timezone, timedelta
from llm.protocol import LLMClient
from db.models.job import Job
from search.filters import SearchFilters
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a job search assistant with web access. Search for job postings matching the criteria provided.

Return a JSON array. Each element must have:
- title: string
- company: string
- posted_at: ISO 8601 datetime string with timezone
- apply_url: string
- raw_description: string (full job description)

Only include jobs posted within the time_window_hours specified. Return ONLY valid JSON array, no markdown."""


class GoogleJobSearcher:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def search(self, filters: SearchFilters) -> list[Job]:
        logger.info(f"Searching Google for jobs in {filters.location}")
        user_message = json.dumps({
            "keywords": filters.keywords,
            "location": filters.location,
            "remote": filters.remote,
            "onsite": filters.onsite,
            "job_type": filters.job_type,
            "time_window_hours": filters.time_window_hours,
        })
        response = self._llm.complete(system=SYSTEM_PROMPT, user=user_message)
        raw_jobs = json.loads(response)
        cutoff = datetime.now(timezone.utc) - timedelta(hours=filters.time_window_hours)
        jobs = []
        for raw in raw_jobs:
            posted_at = datetime.fromisoformat(raw["posted_at"])
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            if posted_at >= cutoff:
                jobs.append(Job(
                    title=raw["title"],
                    company=raw["company"],
                    posted_at=posted_at,
                    source="google",
                    apply_url=raw["apply_url"],
                    raw_description=raw["raw_description"],
                ))
        return jobs
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_google_search.py -v
```

- [x] **Step 4: Commit**

```bash
git add search/google.py
git commit -m "feat: implement GoogleJobSearcher via Claude web search"
```

---

## Task 12: Implement LinkedIn Job Searcher

**Files:**
- Write: `search/linkedin.py`

- [x] **Step 1: Run failing LinkedIn search tests**

```bash
pytest tests/unit/test_linkedin_search.py -v
```

- [x] **Step 2: Implement `search/linkedin.py`**

```python
from datetime import datetime, timezone, timedelta
from apify_client import ApifyClient
from db.models.job import Job
from search.filters import SearchFilters
from utils.logger import get_logger

logger = get_logger(__name__)

LINKEDIN_ACTOR_ID = "curious_coder/linkedin-jobs-scraper"


class LinkedInJobSearcher:
    def __init__(self, api_token: str):
        self._client = ApifyClient(api_token)

    def search(self, filters: SearchFilters) -> list[Job]:
        logger.info(f"Searching LinkedIn via Apify for jobs in {filters.location}")
        run = self._client.actor(LINKEDIN_ACTOR_ID).call(run_input={
            "searchKeywords": " ".join(filters.keywords),
            "location": filters.location,
            "datePosted": "past24Hours",
            "contractType": filters.job_type,
        })
        items = self._client.dataset(run["defaultDatasetId"]).iterate_items()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=filters.time_window_hours)
        jobs = []
        for item in items:
            raw_posted = item.get("postedAt", datetime.now(timezone.utc).isoformat())
            posted_at = datetime.fromisoformat(raw_posted)
            if posted_at.tzinfo is None:
                posted_at = posted_at.replace(tzinfo=timezone.utc)
            if posted_at >= cutoff:
                jobs.append(Job(
                    title=item.get("title", ""),
                    company=item.get("companyName", ""),
                    posted_at=posted_at,
                    source="linkedin",
                    apply_url=item.get("jobUrl", ""),
                    raw_description=item.get("description", ""),
                ))
        return jobs
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_linkedin_search.py -v
```

- [x] **Step 4: Commit**

```bash
git add search/linkedin.py
git commit -m "feat: implement LinkedInJobSearcher via Apify"
```

---

## Task 13: Implement Combiner

**Files:**
- Write: `pipeline/combiner.py`

- [x] **Step 1: Run failing combiner tests**

```bash
pytest tests/unit/test_combiner.py -v
```

- [x] **Step 2: Implement `pipeline/combiner.py`**

```python
from db.models.job import Job
from utils.logger import get_logger

logger = get_logger(__name__)


def combine_jobs(google_jobs: list[Job], linkedin_jobs: list[Job]) -> list[Job]:
    seen: dict[tuple[str, str], Job] = {}
    for job in google_jobs + linkedin_jobs:
        key = (job.title.lower().strip(), job.company.lower().strip())
        if key not in seen:
            seen[key] = job
        else:
            logger.debug(f"Duplicate dropped: {job.title} at {job.company} ({job.source})")
    return list(seen.values())
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_combiner.py -v
```

- [x] **Step 4: Commit**

```bash
git add pipeline/combiner.py
git commit -m "feat: implement job combiner with title+company deduplication"
```

---

## Task 14: Implement Job Scorer

**Files:**
- Write: `scoring/job_scorer.py`

- [x] **Step 1: Run failing job scorer tests**

```bash
pytest tests/unit/test_job_scorer.py -v
```

- [x] **Step 2: Implement `scoring/job_scorer.py`**

```python
import json
from llm.protocol import LLMClient
from db.models.job import Job
from db.models.resume import ResumeProfile
from utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a strict job fit evaluator. Score the job against the candidate's profile.

Be strict — do not inflate scores. Most jobs should score 5-7. Only score 8-10 for near-perfect fit.

Scoring criteria:
- Role match (title, seniority): 0-3 points
- Skills overlap: 0-4 points
- Responsibilities alignment: 0-2 points
- Location/remote fit: 0-1 point

Return ONLY this JSON: {"score": <float 0-10>, "reason": "<one sentence>"}"""


class JobScorer:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def score(self, jobs: list[Job], resume: ResumeProfile) -> list[Job]:
        for job in jobs:
            user_message = json.dumps({
                "job_title": job.title,
                "job_description": job.raw_description,
                "candidate_skills": resume.skills,
                "candidate_seniority": resume.seniority,
                "candidate_experience_years": resume.experience_years,
                "candidate_summary": resume.summary,
            })
            response = self._llm.complete(system=SYSTEM_PROMPT, user=user_message)
            result = json.loads(response)
            job.fit_score = float(result["score"])
            logger.debug(f"Scored '{job.title}' at {job.company}: {job.fit_score}")
        return sorted(jobs, key=lambda j: j.fit_score or 0.0, reverse=True)
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_job_scorer.py -v
```

- [x] **Step 4: Commit**

```bash
git add scoring/job_scorer.py
git commit -m "feat: implement JobScorer with strict LLM scoring"
```

---

## Task 15: Implement Contact Scorer

**Files:**
- Write: `scoring/contact_scorer.py`

- [x] **Step 1: Run failing contact scorer tests**

```bash
pytest tests/unit/test_contact_scorer.py -v
```

- [x] **Step 2: Implement `scoring/contact_scorer.py`**

```python
from db.models.contact import Contact
from utils.logger import get_logger

logger = get_logger(__name__)

CATEGORY_ORDER_STANDARD = {"hiring_manager": 0, "recruiter": 1, "peer": 2, "veteran": 3}
CATEGORY_ORDER_VETERAN = {"veteran": 0, "hiring_manager": 1, "recruiter": 2, "peer": 3}


class ContactScorer:
    def __init__(self, threshold: float, veteran_boost: float):
        self._threshold = threshold
        self._veteran_boost = veteran_boost

    def filter_and_sort(self, contacts: list[Contact], searcher_is_veteran: bool) -> list[Contact]:
        boosted = []
        for contact in contacts:
            score = contact.relevance_score
            if searcher_is_veteran and contact.is_veteran:
                score += self._veteran_boost
                logger.debug(f"Veteran boost applied to {contact.name}: {score}")
            if score >= self._threshold:
                boosted.append(contact.model_copy(update={"relevance_score": score}))

        order = CATEGORY_ORDER_VETERAN if searcher_is_veteran else CATEGORY_ORDER_STANDARD
        return sorted(boosted, key=lambda c: (order.get(c.category, 99), -c.relevance_score))
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_contact_scorer.py -v
```

- [x] **Step 4: Commit**

```bash
git add scoring/contact_scorer.py
git commit -m "feat: implement ContactScorer with veteran boost and category ordering"
```

---

## Task 16: Implement Contact Finder

**Files:**
- Write: `contacts/finder.py`

- [x] **Step 1: Run failing contact finder tests**

```bash
pytest tests/unit/test_contact_finder.py -v
```

- [x] **Step 2: Implement `contacts/finder.py`**

```python
from db.models.contact import Contact
from db.models.job import Job
from utils.logger import get_logger

logger = get_logger(__name__)

CATEGORY_TITLE_SIGNALS = {
    "recruiter": ["recruiter", "talent acquisition", "talent partner", "sourcer"],
    "hiring_manager": ["engineering manager", "director of engineering", "vp of engineering",
                       "head of engineering", "team lead", "tech lead"],
    "peer": [],
}

VETERAN_SIGNALS = ["veteran", "army", "navy", "marines", "air force", "navy",
                   "coast guard", "space force", "military", "sergeant", "captain",
                   "lieutenant", "corporal", "specialist", "mos", "afsc"]


def _infer_category(title: str) -> str:
    title_lower = title.lower()
    for category, signals in CATEGORY_TITLE_SIGNALS.items():
        if any(s in title_lower for s in signals):
            return category
    return "peer"


def _is_veteran_profile(title: str, notes: str = "") -> bool:
    combined = (title + " " + notes).lower()
    return any(signal in combined for signal in VETERAN_SIGNALS)


class ContactFinder:
    def __init__(self, apify_client, vibe_client, max_per_category: int = 8):
        self._apify = apify_client
        self._vibe = vibe_client
        self._max = max_per_category

    def find(self, job: Job) -> list[Contact]:
        logger.info(f"Finding contacts for {job.title} at {job.company}")
        raw_people = self._apify.find_people(company=job.company, job_title=job.title)
        enriched = self._vibe.enrich(raw_people) or raw_people

        contacts: list[Contact] = []
        category_counts: dict[str, int] = {}

        for person in enriched:
            if person.get("company", "").lower() != job.company.lower():
                continue
            category = _infer_category(person.get("title", ""))
            is_vet = _is_veteran_profile(person.get("title", ""))
            if is_vet:
                category = "veteran"

            if category_counts.get(category, 0) >= self._max:
                continue

            contacts.append(Contact(
                name=person["name"],
                title=person["title"],
                company=job.company,
                category=category,
                linkedin_url=person["linkedin_url"],
                email=person.get("email"),
                relevance_score=7.5,
                is_veteran=is_vet,
                notes=person.get("notes", "")[:100],
            ))
            category_counts[category] = category_counts.get(category, 0) + 1

        return contacts
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_contact_finder.py -v
```

- [x] **Step 4: Commit**

```bash
git add contacts/finder.py
git commit -m "feat: implement ContactFinder with 4 categories and veteran detection"
```

---

## Task 17: Implement Message Generator

**Files:**
- Write: `messaging/generator.py`

- [x] **Step 1: Run failing message generator tests**

```bash
pytest tests/unit/test_message_generator.py -v
```

- [x] **Step 2: Implement `messaging/generator.py`**

```python
import json
from llm.protocol import LLMClient
from db.models.contact import Contact
from db.models.job import Job
from db.models.message import Message
from utils.logger import get_logger

logger = get_logger(__name__)

HIRING_MANAGER_SYSTEM = """Write a LinkedIn connection request for a hiring manager. Rules:
- Under 300 characters total
- Reference they are hiring (do NOT say "I applied")
- Highlight 1-2 relevant skills from the job description
- Natural, confident tone
- Mention one SPECIFIC detail from their profile
- Return ONLY the message text, no quotes"""

RECRUITER_SYSTEM = """Write a LinkedIn connection request for an internal recruiter. Rules:
- Under 300 characters total
- Reference the open role at their company (do NOT say "I applied")
- Highlight 1 relevant skill from the job description
- Professional but warm tone
- Mention one SPECIFIC detail from their profile
- Return ONLY the message text, no quotes"""

PEER_SYSTEM = """Write a LinkedIn connection request for a professional peer. Rules:
- Under 300 characters total
- Do NOT mention any job or that you are applying anywhere
- Reference one SPECIFIC detail from their profile (role, company, career move, education, location)
- Focus only on relatability and genuine connection
- If no strong personalisation detail exists, respond with: SKIP
- Return ONLY the message text, no quotes"""

VETERAN_SYSTEM = """Write a LinkedIn connection request for a fellow veteran in tech. Rules:
- Under 300 characters total
- Acknowledge shared military background naturally
- Reference one SPECIFIC detail from their profile or military service
- Focus on connection and shared experience
- Return ONLY the message text, no quotes"""

SYSTEM_PROMPTS = {
    "hiring_manager": HIRING_MANAGER_SYSTEM,
    "recruiter": RECRUITER_SYSTEM,
    "peer": PEER_SYSTEM,
    "veteran": VETERAN_SYSTEM,
}


class MessageGenerator:
    def __init__(self, llm: LLMClient):
        self._llm = llm

    def generate(self, contact: Contact, job: Job) -> Message:
        system = SYSTEM_PROMPTS.get(contact.category, PEER_SYSTEM)
        user = json.dumps({
            "contact_name": contact.name,
            "contact_title": contact.title,
            "contact_company": contact.company,
            "contact_notes": contact.notes,
            "job_title": job.title,
            "job_description": job.raw_description,
        })
        text = self._llm.complete(system=system, user=user)
        if text.strip() == "SKIP":
            text = ""
        text = text[:300]
        logger.debug(f"Generated message for {contact.name} ({contact.category}): {len(text)} chars")
        return Message(contact_id=contact.id, job_id=job.id, message_text=text)
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_message_generator.py -v
```

- [X] **Step 4: Commit**

```bash
git add messaging/generator.py
git commit -m "feat: implement MessageGenerator with category-specific prompts"
```

---

## Task 18: Implement Database Layer

**Files:**
- Write: `db/connection.py`, `db/repositories/job_repo.py`, `db/repositories/contact_repo.py`

- [x] **Step 1: Run failing repository tests**

```bash
pytest tests/unit/test_repositories.py -v
```

- [x] **Step 2: Implement `db/connection.py`**

```python
import asyncpg
from utils.logger import get_logger

logger = get_logger(__name__)


async def create_pool(host: str, port: int, db: str, user: str,
                      password: str, min_size: int = 2, max_size: int = 10):
    logger.info(f"Creating asyncpg pool → {host}:{port}/{db}")
    return await asyncpg.create_pool(
        host=host, port=port, database=db,
        user=user, password=password,
        min_size=min_size, max_size=max_size,
    )
```

- [x] **Step 3: Implement `db/repositories/job_repo.py`**

```python
from db.models.job import Job
from utils.logger import get_logger

logger = get_logger(__name__)

INSERT_JOB = """
INSERT INTO jobs (id, title, company, posted_at, source, apply_url, raw_description, fit_score)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
ON CONFLICT (id) DO NOTHING
"""

SELECT_ALL_JOBS = "SELECT * FROM jobs ORDER BY posted_at DESC"


class JobRepository:
    def __init__(self, pool):
        self._pool = pool

    async def save(self, job: Job) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                INSERT_JOB,
                job.id, job.title, job.company, job.posted_at,
                job.source, job.apply_url, job.raw_description, job.fit_score,
            )
        logger.debug(f"Saved job: {job.title} at {job.company}")

    async def get_all(self) -> list[dict]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(SELECT_ALL_JOBS)
        return [dict(row) for row in rows]
```

- [x] **Step 4: Implement `db/repositories/contact_repo.py`**

```python
from uuid import UUID
from db.models.contact import Contact
from utils.logger import get_logger

logger = get_logger(__name__)

INSERT_CONTACT = """
INSERT INTO contacts (id, job_id, name, title, company, category,
                      linkedin_url, email, relevance_score, is_veteran, notes)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
ON CONFLICT (id) DO NOTHING
"""


class ContactRepository:
    def __init__(self, pool):
        self._pool = pool

    async def save(self, contact: Contact, job_id: UUID) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                INSERT_CONTACT,
                contact.id, job_id, contact.name, contact.title,
                contact.company, contact.category, contact.linkedin_url,
                contact.email, contact.relevance_score, contact.is_veteran, contact.notes,
            )
        logger.debug(f"Saved contact: {contact.name}")
```

- [x] **Step 5: Run tests — all must pass**

```bash
pytest tests/unit/test_repositories.py -v
```

- [x] **Step 6: Commit**

```bash
git add db/
git commit -m "feat: implement asyncpg database layer — connection pool and repositories"
```

---

## Task 19: Implement UI Renderer

**Files:**
- Write: `ui/renderer.py`

- [x] **Step 1: Run failing UI renderer tests**

```bash
pytest tests/unit/test_ui_renderer.py -v
```

- [x] **Step 2: Implement `ui/renderer.py`**

```python
import json
from db.models.job import Job
from db.models.contact import Contact
from db.models.message import Message
from utils.logger import get_logger

logger = get_logger(__name__)


class UIRenderer:
    def render(self, jobs: list[Job], contacts: list[Contact], messages: list[Message]) -> str:
        msg_by_contact = {str(m.contact_id): m.message_text for m in messages}

        job_rows = [
            {
                "role": j.title,
                "company": j.company,
                "posted": j.posted_at.strftime("%Y-%m-%d %H:%M UTC"),
                "source": j.source,
                "score": j.fit_score,
                "apply": j.apply_url,
            }
            for j in jobs
        ]

        contact_rows = [
            {
                "name": c.name,
                "title": c.title,
                "category": c.category,
                "relevance_score": c.relevance_score,
                "linkedin_url": c.linkedin_url,
                "email": c.email,
                "notes": c.notes,
                "message": msg_by_contact.get(str(c.id), ""),
            }
            for c in contacts
        ]

        priority_summary = [
            {
                "priority": i + 1,
                "name": c.name,
                "category": c.category,
                "why": f"{c.title} at {c.company} — relevance {c.relevance_score}",
            }
            for i, c in enumerate(contacts[:10])
        ]

        output = {
            "type": "a2ui",
            "version": "0.8",
            "job_table": {
                "columns": ["#", "role", "company", "posted", "source", "score", "apply"],
                "rows": job_rows,
            },
            "contact_table": {
                "columns": ["#", "name", "title", "category", "relevance_score",
                            "linkedin_url", "email", "notes", "message"],
                "rows": contact_rows,
            },
            "priority_summary": priority_summary,
        }
        logger.info(f"Rendered {len(jobs)} jobs and {len(contacts)} contacts as A2UI JSON")
        return json.dumps(output, indent=2, default=str)
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_ui_renderer.py -v
```

- [x] **Step 4: Commit**

```bash
git add ui/renderer.py
git commit -m "feat: implement A2UI JSON renderer"
```

---

## Task 20: Implement Orchestrator

**Files:**
- Write: `pipeline/orchestrator.py`

- [x] **Step 1: Run failing orchestrator tests**

```bash
pytest tests/unit/test_orchestrator.py -v
```

- [x] **Step 2: Implement `pipeline/orchestrator.py`**

```python
import asyncio
from pathlib import Path
from pipeline.state import PipelineState, PipelineContext
from search.filters import SearchFilters
from utils.logger import get_logger

logger = get_logger(__name__)


class Orchestrator:
    def __init__(self, *, cv_loader, cv_parser, google_searcher, linkedin_searcher,
                 combiner, job_scorer, contact_finder, contact_scorer,
                 message_generator, job_repo, contact_repo, renderer,
                 job_threshold: float, contact_threshold: float, top_n: int):
        self._cv_loader = cv_loader
        self._cv_parser = cv_parser
        self._google = google_searcher
        self._linkedin = linkedin_searcher
        self._combiner = combiner
        self._job_scorer = job_scorer
        self._contact_finder = contact_finder
        self._contact_scorer = contact_scorer
        self._msg_gen = message_generator
        self._job_repo = job_repo
        self._contact_repo = contact_repo
        self._renderer = renderer
        self._job_threshold = job_threshold
        self._contact_threshold = contact_threshold
        self._top_n = top_n

    async def run(self, cv_path: str | Path, filters: SearchFilters) -> PipelineContext:
        ctx = PipelineContext()
        try:
            ctx.state = PipelineState.LOADING_CV
            raw_cv = self._cv_loader.load(cv_path)
            ctx.resume = self._cv_parser.parse(raw_cv)
            ctx.filters = filters

            ctx.state = PipelineState.SEARCHING
            google_jobs, linkedin_jobs = await asyncio.gather(
                asyncio.to_thread(self._google.search, filters),
                asyncio.to_thread(self._linkedin.search, filters),
            )
            ctx.jobs = self._combiner(google_jobs, linkedin_jobs)

            ctx.state = PipelineState.SCORING_JOBS
            ctx.jobs = self._job_scorer.score(ctx.jobs, ctx.resume)
            top_jobs = [j for j in ctx.jobs if (j.fit_score or 0) > self._job_threshold][:self._top_n]

            ctx.state = PipelineState.SAVING
            for job in top_jobs:
                await self._job_repo.save(job)

            ctx.state = PipelineState.FINDING_CONTACTS
            raw_contacts = []
            for job in top_jobs:
                raw_contacts.extend(self._contact_finder.find(job))

            ctx.state = PipelineState.SCORING_CONTACTS
            ctx.contacts = self._contact_scorer.filter_and_sort(
                raw_contacts, searcher_is_veteran=ctx.resume.is_veteran
            )

            ctx.state = PipelineState.GENERATING_MESSAGES
            ctx.messages = [self._msg_gen.generate(c, j) for c in ctx.contacts for j in top_jobs[:1]]

            ctx.state = PipelineState.SAVING
            for contact in ctx.contacts:
                await self._contact_repo.save(contact, top_jobs[0].id if top_jobs else None)

            ctx.state = PipelineState.RENDERING
            result = self._renderer.render(
                jobs=top_jobs, contacts=ctx.contacts, messages=ctx.messages
            )
            print(result)

            ctx.state = PipelineState.COMPLETE

        except Exception as exc:
            logger.error(f"Pipeline failed: {exc}", exc_info=True)
            ctx.errors.append(str(exc))
            ctx.state = PipelineState.ERROR

        return ctx
```

- [x] **Step 3: Run tests — all must pass**

```bash
pytest tests/unit/test_orchestrator.py -v
```

- [x] **Step 4: Run the full unit test suite — all must pass**

```bash
pytest tests/unit/ -v --tb=short
```

Expected: all green.

- [x] **Step 5: Commit**

```bash
git add pipeline/orchestrator.py
git commit -m "feat: implement pipeline Orchestrator with async search and state management"
```

---

## Task 21: Implement CLI and Scheduler

**Files:**
- Write: `cli.py`, `scheduler.py`

- [x] **Step 1: Implement `cli.py`**

```python
import asyncio
import argparse
import os
from hydra import initialize, compose
from omegaconf import OmegaConf

from cv.loader import CVLoader
from cv.parser import CVParser
from llm.claude import ClaudeClient
from search.filters import SearchFilters
from search.google import GoogleJobSearcher
from search.linkedin import LinkedInJobSearcher
from pipeline.combiner import combine_jobs
from scoring.job_scorer import JobScorer
from scoring.contact_scorer import ContactScorer
from contacts.finder import ContactFinder
from messaging.generator import MessageGenerator
from db.connection import create_pool
from db.repositories.job_repo import JobRepository
from db.repositories.contact_repo import ContactRepository
from ui.renderer import UIRenderer
from pipeline.orchestrator import Orchestrator
from utils.logger import get_logger

logger = get_logger(__name__)


def build_orchestrator(cfg) -> Orchestrator:
    llm = ClaudeClient(api_key=cfg.anthropic_api_key)
    return Orchestrator(
        cv_loader=CVLoader(),
        cv_parser=CVParser(llm=llm),
        google_searcher=GoogleJobSearcher(llm=llm),
        linkedin_searcher=LinkedInJobSearcher(api_token=cfg.apify_api_token),
        combiner=combine_jobs,
        job_scorer=JobScorer(llm=llm),
        contact_finder=ContactFinder(
            apify_client=None,
            vibe_client=None,
            max_per_category=cfg.scoring.max_contacts_per_category,
        ),
        contact_scorer=ContactScorer(
            threshold=cfg.scoring.contact_score_threshold,
            veteran_boost=cfg.scoring.veteran_score_boost,
        ),
        message_generator=MessageGenerator(llm=llm),
        job_repo=None,
        contact_repo=None,
        renderer=UIRenderer(),
        job_threshold=cfg.scoring.job_score_threshold,
        contact_threshold=cfg.scoring.contact_score_threshold,
        top_n=cfg.scoring.top_n_jobs,
    )


async def run_full(cfg, cv_path: str, keywords: list[str]):
    pool = await create_pool(
        host=cfg.database.host, port=int(cfg.database.port),
        db=cfg.database.db, user=cfg.database.user,
        password=cfg.database.password,
    )
    llm = ClaudeClient(api_key=cfg.anthropic_api_key)
    orch = Orchestrator(
        cv_loader=CVLoader(),
        cv_parser=CVParser(llm=llm),
        google_searcher=GoogleJobSearcher(llm=llm),
        linkedin_searcher=LinkedInJobSearcher(api_token=cfg.apify_api_token),
        combiner=combine_jobs,
        job_scorer=JobScorer(llm=llm),
        contact_finder=ContactFinder(apify_client=None, vibe_client=None,
                                     max_per_category=cfg.scoring.max_contacts_per_category),
        contact_scorer=ContactScorer(threshold=cfg.scoring.contact_score_threshold,
                                     veteran_boost=cfg.scoring.veteran_score_boost),
        message_generator=MessageGenerator(llm=llm),
        job_repo=JobRepository(pool=pool),
        contact_repo=ContactRepository(pool=pool),
        renderer=UIRenderer(),
        job_threshold=cfg.scoring.job_score_threshold,
        contact_threshold=cfg.scoring.contact_score_threshold,
        top_n=cfg.scoring.top_n_jobs,
    )
    filters = SearchFilters(
        keywords=keywords or cfg.search.keywords,
        location=cfg.search.location,
        remote=cfg.search.remote,
        onsite=cfg.search.onsite,
        job_type=cfg.search.job_type,
        time_window_hours=cfg.search.time_window_hours,
    )
    await orch.run(cv_path=cv_path, filters=filters)
    await pool.close()


def main():
    parser = argparse.ArgumentParser(description="Job Search Agent")
    parser.add_argument("mode", choices=["search", "full", "contacts-only"],
                        help="Pipeline mode")
    parser.add_argument("--cv", required=True, help="Path to resume PDF")
    parser.add_argument("--keywords", nargs="*", default=[], help="Search keywords")
    args = parser.parse_args()

    with initialize(config_path="config", version_base=None):
        cfg = compose(config_name="config")

    if args.mode == "full":
        asyncio.run(run_full(cfg, cv_path=args.cv, keywords=args.keywords))
    else:
        logger.info(f"Mode '{args.mode}' not yet implemented — use 'full'")


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Implement `scheduler.py`**

```python
import asyncio
import time
from utils.logger import get_logger

logger = get_logger(__name__)


def run_on_schedule(interval_seconds: int, cv_path: str, keywords: list[str], cfg):
    from cli import run_full
    logger.info(f"Scheduler started — running every {interval_seconds}s")
    while True:
        logger.info("Scheduler: starting pipeline run")
        asyncio.run(run_full(cfg=cfg, cv_path=cv_path, keywords=keywords))
        logger.info(f"Scheduler: run complete — sleeping {interval_seconds}s")
        time.sleep(interval_seconds)
```

- [x] **Step 3: Run the full unit test suite one final time**

```bash
pytest tests/unit/ -v --tb=short
```
Expected: all green.

- [x] **Step 4: Commit**

```bash
git add cli.py scheduler.py
git commit -m "feat: implement CLI entry point and scheduler"
```

---

## Task 22: Integration Test Skeleton

**Files:**
- Write: `tests/integration/test_pipeline.py`

- [x] **Step 1: Write integration test skeleton**

```python
"""
Integration tests — hit real APIs. Run manually only:
    pytest tests/integration/ -v

Requires all environment variables to be set (see .env.example).
DO NOT run in CI.
"""
import pytest
import asyncio
import os
from pathlib import Path


@pytest.mark.integration
def test_full_pipeline_runs_end_to_end():
    """Run the full pipeline with real APIs against a sample resume."""
    pytest.skip("Run manually: set env vars and provide a real resume PDF")


@pytest.mark.integration
def test_google_search_returns_jobs():
    pytest.skip("Run manually: requires ANTHROPIC_API_KEY")


@pytest.mark.integration
def test_linkedin_search_returns_jobs():
    pytest.skip("Run manually: requires APIFY_API_TOKEN")
```

- [x] **Step 2: Commit**

```bash
git add tests/integration/test_pipeline.py
git commit -m "test: add integration test skeleton (manual run only)"
```

---

## Final Verification

- [x] **Run full test suite and confirm all unit tests pass**

```bash
pytest tests/unit/ -v --cov=. --cov-report=term-missing --ignore=tests/integration
```

- [x] **Confirm project structure is correct**

```bash
find . -name "*.py" | grep -v __pycache__ | sort
```

- [x] **Tag the working baseline**

```bash
git tag v0.1.0-foundation
```
