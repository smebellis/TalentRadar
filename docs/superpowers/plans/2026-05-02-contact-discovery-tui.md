# Contact Discovery & Textual TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace broken Apify contact discovery with Vibe Prospecting REST API calls, and add a live Textual TUI dashboard that updates in real-time as each pipeline stage completes.

**Architecture:** `VibeProspectingClient` gains a `find_people()` method using a two-step REST flow (match company → fetch prospects). `Orchestrator` gets an optional `progress_callback`. `JobSearchApp` (Textual) owns the asyncio event loop, runs the Orchestrator as an async coroutine worker, and updates four panel widgets in real-time via the callback.

**Tech Stack:** textual>=0.50.0, httpx (existing), pytest-asyncio (existing)

---

## File Map

**Create:**
- `tests/unit/test_vibe_client.py` — find_people() unit tests
- `ui/widgets/__init__.py` — empty package marker
- `ui/widgets/progress_panel.py` — ProgressPanel widget
- `ui/widgets/jobs_table.py` — JobsTable widget
- `ui/widgets/contacts_table.py` — ContactsTable widget
- `ui/widgets/messages_panel.py` — MessagesPanel widget
- `ui/tui.py` — JobSearchApp Textual application
- `tests/unit/test_tui.py` — TUI unit tests

**Modify:**
- `requirements.txt` — add `textual>=0.50.0`
- `config/api_keys.yaml` — add `vibe_api_base_url`
- `.env` — add `VIBE_API_BASE_URL`
- `contacts/clients.py` — add `find_people()` to `VibeProspectingClient`
- `contacts/finder.py` — update `find()` to call `vibe_client.find_people()` directly
- `tests/unit/test_contact_finder.py` — update tests to assert vibe path, not apify
- `pipeline/orchestrator.py` — add `progress_callback` parameter, fire at each stage
- `cli.py` — pass `base_url=cfg.vibe_api_base_url`, swap `full` mode to `JobSearchApp`

---

## Task 1: Setup — textual, config, env

**Files:**
- Modify: `requirements.txt`
- Modify: `config/api_keys.yaml`
- Modify: `.env`
- Modify: `cli.py`

- [ ] **Step 1: Add textual to requirements.txt**

  Open `requirements.txt` and add after `httpx`:
  ```
  textual>=0.50.0
  ```

- [ ] **Step 2: Install it**

  Run:
  ```bash
  pip install textual>=0.50.0
  ```
  Expected: installs without error.

- [ ] **Step 3: Add vibe_api_base_url to config/api_keys.yaml**

  Current file:
  ```yaml
  anthropic_api_key: ${oc.env:ANTHROPIC_API_KEY}
  apify_api_token: ${oc.env:APIFY_API_TOKEN}
  vibe_api_key: ${oc.env:VIBE_API_KEY}
  ```

  Add one line at the end:
  ```yaml
  vibe_api_base_url: ${oc.env:VIBE_API_BASE_URL,}
  ```
  The trailing `,` means the value defaults to empty string when the env var is unset (Hydra OmegaConf syntax).

- [ ] **Step 4: Add VIBE_API_BASE_URL to .env**

  Append to `.env`:
  ```
  VIBE_API_BASE_URL=https://api.explorium.ai/v1
  ```

- [ ] **Step 5: Update cli.py to pass base_url to VibeProspectingClient**

  In `build_orchestrator()`, change:
  ```python
  vibe_client = VibeProspectingClient(api_key=cfg.vibe_api_key)
  ```
  to:
  ```python
  vibe_client = VibeProspectingClient(api_key=cfg.vibe_api_key, base_url=cfg.vibe_api_base_url)
  ```

  In `run_full()`, make the same change (same line, same fix).

- [ ] **Step 6: Run existing tests to confirm nothing broke**

  Run:
  ```bash
  pytest tests/unit/ -v -x
  ```
  Expected: all tests pass.

- [ ] **Step 7: Commit**

  ```bash
  git add requirements.txt config/api_keys.yaml .env cli.py
  git commit -m "feat: add textual dep, vibe_api_base_url config"
  ```

---

## Task 2: VibeProspectingClient.find_people() (TDD)

**Files:**
- Create: `tests/unit/test_vibe_client.py`
- Modify: `contacts/clients.py`

**Note on REST endpoints:** The Explorium REST API uses two endpoints for prospect search. Based on live verification of the MCP tool schema, the field names in the prospect response are `prospect_full_name`, `prospect_job_title`, `prospect_linkedin`, `prospect_city`, and `prospect_region_name`. The endpoint paths assumed here are `/businesses/match` and `/prospects/fetch`. If either returns 404, check the Explorium REST API docs at https://api.explorium.ai — the existing `enrich()` method in `contacts/clients.py` shows the correct auth header pattern to follow.

- [ ] **Step 1: Write failing tests**

  Create `tests/unit/test_vibe_client.py`:

  ```python
  from unittest.mock import MagicMock, patch

  import pytest

  from contacts.clients import VibeProspectingClient


  def _make_client():
      return VibeProspectingClient(
          api_key="test-key", base_url="https://api.explorium.ai/v1"
      )


  def _mock_match_response(business_id="abc123"):
      resp = MagicMock()
      resp.status_code = 200
      resp.json.return_value = {
          "matched_businesses": [{"business_id": business_id}]
      }
      resp.raise_for_status = MagicMock()
      return resp


  def _mock_fetch_response(people):
      resp = MagicMock()
      resp.status_code = 200
      resp.json.return_value = {
          "preview": {"preview_data": people}
      }
      resp.raise_for_status = MagicMock()
      return resp


  def test_find_people_maps_response_correctly():
      client = _make_client()
      raw_person = {
          "prospect_full_name": "Jane Smith",
          "prospect_job_title": "Engineering Manager",
          "prospect_linkedin": "linkedin.com/in/janesmith",
          "prospect_company_name": "Acme Corp",
          "prospect_city": "denver",
          "prospect_region_name": "colorado",
      }
      match_resp = _mock_match_response("biz-1")
      fetch_resp = _mock_fetch_response([raw_person])

      with patch("contacts.clients.httpx.Client") as mock_cls:
          mock_http = MagicMock()
          mock_cls.return_value.__enter__.return_value = mock_http
          mock_http.post.side_effect = [match_resp, fetch_resp]

          result = client.find_people("Acme Corp", "Engineer")

      assert len(result) == 1
      p = result[0]
      assert p["name"] == "Jane Smith"
      assert p["title"] == "Engineering Manager"
      assert p["linkedin_url"] == "https://linkedin.com/in/janesmith"
      assert p["company"] == "Acme Corp"
      assert p["email"] is None
      assert "denver" in p["notes"]


  def test_find_people_returns_empty_when_base_url_unset():
      client = VibeProspectingClient(api_key="test-key", base_url=None)
      result = client.find_people("Acme Corp", "Engineer")
      assert result == []


  def test_find_people_returns_empty_when_api_key_unset():
      client = VibeProspectingClient(api_key=None, base_url="https://api.explorium.ai/v1")
      result = client.find_people("Acme Corp", "Engineer")
      assert result == []


  def test_find_people_returns_empty_on_http_error():
      client = _make_client()

      with patch("contacts.clients.httpx.Client") as mock_cls:
          mock_http = MagicMock()
          mock_cls.return_value.__enter__.return_value = mock_http
          mock_http.post.side_effect = Exception("connection error")

          result = client.find_people("Acme Corp", "Engineer")

      assert result == []


  def test_find_people_returns_empty_on_402():
      client = _make_client()
      resp_402 = MagicMock()
      resp_402.status_code = 402
      resp_402.raise_for_status = MagicMock()
      resp_402.json.return_value = {}

      with patch("contacts.clients.httpx.Client") as mock_cls:
          mock_http = MagicMock()
          mock_cls.return_value.__enter__.return_value = mock_http
          mock_http.post.return_value = resp_402

          result = client.find_people("Acme Corp", "Engineer")

      assert result == []


  def test_find_people_returns_empty_when_no_business_match():
      client = _make_client()
      no_match_resp = MagicMock()
      no_match_resp.status_code = 200
      no_match_resp.json.return_value = {"matched_businesses": []}
      no_match_resp.raise_for_status = MagicMock()

      with patch("contacts.clients.httpx.Client") as mock_cls:
          mock_http = MagicMock()
          mock_cls.return_value.__enter__.return_value = mock_http
          mock_http.post.return_value = no_match_resp

          result = client.find_people("Unknown Corp", "Engineer")

      assert result == []
  ```

- [ ] **Step 2: Run tests to verify they fail**

  Run:
  ```bash
  pytest tests/unit/test_vibe_client.py -v
  ```
  Expected: `AttributeError: 'VibeProspectingClient' object has no attribute 'find_people'`

- [ ] **Step 3: Implement find_people() in contacts/clients.py**

  Add the following import at the top of `contacts/clients.py` (already has `get_logger` potential — add it):
  ```python
  import logging
  logger = logging.getLogger(__name__)
  ```

  Add `find_people()` as a new method of `VibeProspectingClient`, after the existing `enrich()`:

  ```python
  def find_people(self, company: str, job_title: str, max_results: int = 20) -> list[dict]:
      if not self.base_url or not self.api_key:
          logger.warning("VibeProspectingClient: base_url or api_key not configured")
          return []

      headers = {
          "Authorization": f"Bearer {self.api_key}",
          "Content-Type": "application/json",
      }
      base = self.base_url.rstrip("/")

      try:
          with httpx.Client(timeout=30.0) as client:
              # Step 1: resolve company name → business_id
              match_resp = client.post(
                  f"{base}/businesses/match",
                  headers=headers,
                  json={"businesses": [{"name": company}]},
              )
              if match_resp.status_code == 402:
                  logger.warning("VibeProspectingClient: credits exhausted (match)")
                  return []
              match_resp.raise_for_status()
              matches = match_resp.json().get("matched_businesses") or []
              if not matches:
                  logger.warning("VibeProspectingClient: no match for company %r", company)
                  return []
              business_id = matches[0]["business_id"]

              # Step 2: fetch prospects for that business
              fetch_resp = client.post(
                  f"{base}/prospects/fetch",
                  headers=headers,
                  json={
                      "filters": {"business_id": {"values": [business_id]}},
                      "number_of_results": max_results,
                  },
              )
              if fetch_resp.status_code == 402:
                  logger.warning("VibeProspectingClient: credits exhausted (fetch)")
                  return []
              fetch_resp.raise_for_status()
              data = fetch_resp.json()
      except Exception as exc:
          logger.warning("VibeProspectingClient.find_people failed: %s", exc)
          return []

      raw_people = (
          (data.get("preview") or {}).get("preview_data")
          or data.get("prospects")
          or data.get("data")
          or []
      )

      prospects: list[dict] = []
      for p in raw_people:
          linkedin = p.get("prospect_linkedin") or ""
          if linkedin and not linkedin.startswith("http"):
              linkedin = "https://" + linkedin
          city = p.get("prospect_city") or ""
          region = p.get("prospect_region_name") or ""
          notes = ", ".join(filter(None, [city, region]))[:100]
          prospects.append(
              {
                  "name": p.get("prospect_full_name") or "",
                  "title": p.get("prospect_job_title") or "",
                  "company": company,
                  "linkedin_url": linkedin,
                  "email": None,
                  "notes": notes,
              }
          )

      return prospects
  ```

- [ ] **Step 4: Run tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_vibe_client.py -v
  ```
  Expected: all 6 tests pass.

- [ ] **Step 5: Run full suite to confirm no regressions**

  Run:
  ```bash
  pytest tests/unit/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add contacts/clients.py tests/unit/test_vibe_client.py
  git commit -m "feat: add VibeProspectingClient.find_people() with two-step Explorium REST flow"
  ```

---

## Task 3: ContactFinder.find() update (TDD)

**Files:**
- Modify: `tests/unit/test_contact_finder.py`
- Modify: `contacts/finder.py`

The existing tests feed data via `mock_apify.find_people`. After this task, `find()` calls `vibe_client.find_people()` directly and never touches `apify_client`. The `apify_client` constructor parameter stays (no broken callers) but is ignored in `find()`.

- [ ] **Step 1: Update test_contact_finder.py to test the vibe path**

  Replace the full contents of `tests/unit/test_contact_finder.py`:

  ```python
  from datetime import datetime, timezone
  from unittest.mock import MagicMock

  import pytest

  from contacts.finder import ContactFinder
  from db.models.job import Job


  def _make_job():
      return Job(
          title="Senior Engineer",
          company="TechCorp",
          posted_at=datetime.now(timezone.utc),
          source="google",
          apply_url="https://example.com",
          raw_description="Python role",
      )


  def _make_finder(vibe_people, max_per_category=8):
      mock_apify = MagicMock()
      mock_vibe = MagicMock()
      mock_vibe.find_people.return_value = vibe_people
      return ContactFinder(
          apify_client=mock_apify,
          vibe_client=mock_vibe,
          max_per_category=max_per_category,
      ), mock_apify, mock_vibe


  def test_contact_finder_calls_vibe_find_people():
      finder, mock_apify, mock_vibe = _make_finder([])
      finder.find(_make_job())
      mock_vibe.find_people.assert_called_once_with(
          company="TechCorp", job_title="Senior Engineer"
      )


  def test_contact_finder_does_not_call_apify():
      finder, mock_apify, mock_vibe = _make_finder([])
      finder.find(_make_job())
      mock_apify.find_people.assert_not_called()


  def test_contact_finder_returns_contacts_for_job():
      people = [
          {
              "name": "Jane",
              "title": "Engineering Manager",
              "linkedin_url": "https://linkedin.com/in/jane",
              "company": "TechCorp",
              "email": None,
              "notes": "denver, colorado",
          },
      ]
      finder, _, _ = _make_finder(people)
      result = finder.find(_make_job())
      assert len(result) >= 1


  def test_contact_finder_only_includes_current_employees():
      people = [
          {
              "name": "Bob",
              "title": "Former Manager",
              "linkedin_url": "https://linkedin.com/in/bob",
              "company": "OtherCorp",
              "email": None,
              "notes": "",
          },
      ]
      finder, _, _ = _make_finder(people)
      result = finder.find(_make_job())
      for contact in result:
          assert contact.company == "TechCorp"


  def test_contact_finder_respects_max_per_category():
      many_people = [
          {
              "name": f"Person {i}",
              "title": "Recruiter",
              "linkedin_url": f"https://linkedin.com/in/p{i}",
              "company": "TechCorp",
              "email": None,
              "notes": "",
          }
          for i in range(20)
      ]
      finder, _, _ = _make_finder(many_people, max_per_category=3)
      result = finder.find(_make_job())
      recruiters = [c for c in result if c.category == "recruiter"]
      assert len(recruiters) <= 3
  ```

- [ ] **Step 2: Run tests to verify they fail**

  Run:
  ```bash
  pytest tests/unit/test_contact_finder.py -v
  ```
  Expected: `test_contact_finder_calls_vibe_find_people` and `test_contact_finder_does_not_call_apify` fail.

- [ ] **Step 3: Update ContactFinder.find() in contacts/finder.py**

  Replace the `find()` method body:

  ```python
  def find(self, job: Job):
      raw_people = (
          self.vibe_client.find_people(company=job.company, job_title=job.title)
          or []
      )
      contacts: list[Contact] = []
      category_counts: dict[str, int] = {}

      for person in raw_people:
          if person.get("company", "").lower() != job.company.lower():
              continue
          category = _infer_category(person.get("title", ""))
          is_vet = _is_veteran_profile(person.get("title", ""))
          if is_vet:
              category = "veteran"

          if category_counts.get(category, 0) >= self.max_per_category:
              continue

          contacts.append(
              Contact(
                  name=person["name"],
                  title=person["title"],
                  company=job.company,
                  category=category,
                  linkedin_url=person["linkedin_url"],
                  email=person.get("email"),
                  relevance_score=7.5,
                  is_veteran=is_vet,
                  notes=person.get("notes", "")[:100],
              )
          )
          category_counts[category] = category_counts.get(category, 0) + 1

      return contacts
  ```

  The `enrich` call that was there before is removed. The `_NoopVibeClient` stub in the same file still needs a `find_people` method to avoid AttributeError. Update it:

  ```python
  class _NoopVibeClient:
      def find_people(self, company: str, job_title: str) -> list[dict]:
          return []

      def enrich(self, people: list[dict]) -> list[dict]:
          return people
  ```

- [ ] **Step 4: Run tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_contact_finder.py -v
  ```
  Expected: all 5 tests pass.

- [ ] **Step 5: Run full suite**

  Run:
  ```bash
  pytest tests/unit/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add contacts/finder.py tests/unit/test_contact_finder.py
  git commit -m "feat: ContactFinder.find() uses vibe_client.find_people() directly, drops Apify path"
  ```

---

## Task 4: Orchestrator progress_callback (TDD)

**Files:**
- Modify: `tests/unit/test_orchestrator.py` — add callback tests
- Modify: `pipeline/orchestrator.py` — add progress_callback parameter and fire calls

The callback signature is `progress_callback(stage: str, data: dict) -> None`. Existing tests pass `progress_callback=None` implicitly (it defaults to `None`) so they need no changes. New tests verify callback is fired at the right stages with the right data shapes.

- [ ] **Step 1: Add failing callback tests to test_orchestrator.py**

  Read the current `tests/unit/test_orchestrator.py` first (do NOT replace it — append). At the end of the file, add:

  ```python
  @pytest.mark.asyncio
  async def test_orchestrator_fires_progress_callback_at_each_stage():
      """Callback is called for each pipeline stage with the stage name."""
      from unittest.mock import AsyncMock, MagicMock, call
      from pipeline.state import PipelineState

      fired_stages = []

      def callback(stage, data):
          fired_stages.append(stage)

      job = _make_job(score=8.0)
      contact = _make_contact()

      cv_loader = MagicMock()
      cv_loader.load.return_value = "raw cv text"
      cv_parser = MagicMock()
      cv_parser.parse.return_value = MagicMock(is_veteran=False)
      google = MagicMock()
      google.search.return_value = [job]
      linkedin = MagicMock()
      linkedin.search.return_value = []
      job_scorer = MagicMock()
      job_scorer.score.return_value = [job]
      contact_finder = MagicMock()
      contact_finder.find.return_value = [contact]
      contact_scorer = MagicMock()
      contact_scorer.filter_and_sort.return_value = [contact]
      msg_gen = MagicMock()
      msg_gen.generate.return_value = "Hi there"
      job_repo = AsyncMock()
      contact_repo = AsyncMock()
      renderer = MagicMock()
      renderer.render.return_value = '{"output": "test"}'

      orch = Orchestrator(
          cv_loader=cv_loader,
          cv_parser=cv_parser,
          google_searcher=google,
          linkedin_searcher=linkedin,
          combiner=combine_jobs,
          job_scorer=job_scorer,
          contact_finder=contact_finder,
          contact_scorer=contact_scorer,
          message_generator=msg_gen,
          job_repo=job_repo,
          contact_repo=contact_repo,
          renderer=renderer,
          job_threshold=5.0,
          contact_threshold=5.0,
          top_n=5,
          progress_callback=callback,
      )
      filters = SearchFilters(
          keywords=["python"],
          location="Denver",
          remote=True,
          onsite=False,
          job_type="full_time",
          time_window_hours=48,
      )
      ctx = await orch.run(cv_path="resume.pdf", filters=filters)

      assert "loading_cv" in fired_stages
      assert "searching" in fired_stages
      assert "scoring_jobs" in fired_stages
      assert "finding_contacts" in fired_stages
      assert "scoring_contacts" in fired_stages
      assert "generating_messages" in fired_stages
      assert "complete" in fired_stages


  @pytest.mark.asyncio
  async def test_orchestrator_callback_receives_jobs_at_scoring_stage():
      from unittest.mock import AsyncMock, MagicMock

      received = {}

      def callback(stage, data):
          received[stage] = data

      job = _make_job(score=8.0)
      contact = _make_contact()

      cv_loader = MagicMock()
      cv_loader.load.return_value = "raw cv text"
      cv_parser = MagicMock()
      cv_parser.parse.return_value = MagicMock(is_veteran=False)
      google = MagicMock()
      google.search.return_value = [job]
      linkedin = MagicMock()
      linkedin.search.return_value = []
      job_scorer = MagicMock()
      job_scorer.score.return_value = [job]
      contact_finder = MagicMock()
      contact_finder.find.return_value = [contact]
      contact_scorer = MagicMock()
      contact_scorer.filter_and_sort.return_value = [contact]
      msg_gen = MagicMock()
      msg_gen.generate.return_value = "Hi there"
      job_repo = AsyncMock()
      contact_repo = AsyncMock()
      renderer = MagicMock()
      renderer.render.return_value = '{"output": "test"}'

      orch = Orchestrator(
          cv_loader=cv_loader,
          cv_parser=cv_parser,
          google_searcher=google,
          linkedin_searcher=linkedin,
          combiner=combine_jobs,
          job_scorer=job_scorer,
          contact_finder=contact_finder,
          contact_scorer=contact_scorer,
          message_generator=msg_gen,
          job_repo=job_repo,
          contact_repo=contact_repo,
          renderer=renderer,
          job_threshold=5.0,
          contact_threshold=5.0,
          top_n=5,
          progress_callback=callback,
      )
      filters = SearchFilters(
          keywords=["python"],
          location="Denver",
          remote=True,
          onsite=False,
          job_type="full_time",
          time_window_hours=48,
      )
      await orch.run(cv_path="resume.pdf", filters=filters)

      assert "top_jobs" in received.get("scoring_jobs", {})
      assert "contacts" in received.get("scoring_contacts", {})
      assert "messages" in received.get("generating_messages", {})
  ```

  **Note:** The test helpers `_make_job` and `_make_contact` must already exist in `test_orchestrator.py`. Read the file before appending to verify those helper names match exactly.

- [ ] **Step 2: Run new tests to verify they fail**

  Run:
  ```bash
  pytest tests/unit/test_orchestrator.py::test_orchestrator_fires_progress_callback_at_each_stage -v
  ```
  Expected: `TypeError: Orchestrator.__init__() got an unexpected keyword argument 'progress_callback'`

- [ ] **Step 3: Add progress_callback to Orchestrator.__init__ and fire calls in run()**

  In `pipeline/orchestrator.py`, update `__init__` to accept the new parameter. Add it as the last keyword argument:

  ```python
  def __init__(
      self,
      *,
      cv_loader,
      cv_parser,
      google_searcher,
      linkedin_searcher,
      combiner,
      job_scorer,
      contact_finder,
      contact_scorer,
      message_generator,
      job_repo,
      contact_repo,
      renderer,
      job_threshold: float,
      contact_threshold: float,
      top_n: int,
      progress_callback=None,
  ):
      # ... existing assignments ...
      self._progress_callback = progress_callback
  ```

  Add a private helper at the bottom of `__init__`, then call it from `run()`. Replace each `print(...)` call in `run()` with a callback fire AND the existing print (so non-TUI callers still see output):

  ```python
  def _fire(self, stage: str, data: dict) -> None:
      if self._progress_callback:
          self._progress_callback(stage, data)
  ```

  Update `run()` to fire callbacks at each stage. The full updated `run()` method:

  ```python
  async def run(self, cv_path: str | Path, filters: SearchFilters) -> PipelineContext:
      ctx = PipelineContext()
      try:
          ctx.state = PipelineState.LOADING_CV
          print("[1/7] Loading and parsing CV...", flush=True)
          self._fire("loading_cv", {})
          raw_cv = self._cv_loader.load(cv_path)
          ctx.resume = self._cv_parser.parse(raw_cv)
          ctx.filters = filters

          ctx.state = PipelineState.SEARCHING
          print("[2/7] Searching Google and LinkedIn...", flush=True)
          self._fire("searching", {})
          google_jobs, linkedin_jobs = await asyncio.gather(
              asyncio.to_thread(self._google.search, filters),
              asyncio.to_thread(self._linkedin.search, filters),
          )
          ctx.jobs = self._combiner(google_jobs, linkedin_jobs)
          print(
              f"  Found {len(ctx.jobs)} jobs (google={len(google_jobs)}, linkedin={len(linkedin_jobs)})",
              flush=True,
          )

          ctx.state = PipelineState.SCORING_JOBS
          print(f"[3/7] Scoring {len(ctx.jobs)} jobs...", flush=True)
          ctx.jobs = self._job_scorer.score(ctx.jobs, ctx.resume)
          top_jobs = [
              j for j in ctx.jobs if (j.fit_score or 0) > self._job_threshold
          ][: self._top_n]
          print(
              f"  {len(top_jobs)} jobs scored above threshold {self._job_threshold}",
              flush=True,
          )
          self._fire("scoring_jobs", {"top_jobs": top_jobs})

          for job in top_jobs:
              await self._job_repo.save(job)

          ctx.state = PipelineState.FINDING_CONTACTS
          print(f"[4/7] Finding contacts for {len(top_jobs)} top jobs...", flush=True)
          self._fire("finding_contacts", {})
          raw_contacts = []
          for job in top_jobs:
              raw_contacts.extend(self._contact_finder.find(job))

          ctx.state = PipelineState.SCORING_CONTACTS
          print(f"[5/7] Scoring {len(raw_contacts)} contacts...", flush=True)
          ctx.contacts = self._contact_scorer.filter_and_sort(
              raw_contacts, searcher_is_veteran=ctx.resume.is_veteran
          )
          self._fire("scoring_contacts", {"contacts": ctx.contacts})

          ctx.state = PipelineState.GENERATE_MESSAGES
          print(f"[6/7] Generating messages for {len(ctx.contacts)} contacts...", flush=True)
          ctx.messages = [
              self._msg_gen.generate(c, j) for c in ctx.contacts for j in top_jobs[:1]
          ]
          self._fire("generating_messages", {"messages": ctx.messages})

          for contact in ctx.contacts:
              await self._contact_repo.save(
                  contact,
                  top_jobs[0].id if top_jobs else None,
              )

          print("[7/7] Rendering output...", flush=True)
          ctx.output = self._renderer.render(
              jobs=top_jobs, contacts=ctx.contacts, messages=ctx.messages
          )

          ctx.state = PipelineState.COMPLETE
          print("Pipeline complete.", flush=True)
          self._fire("complete", {})

      except Exception as exc:
          ctx.errors.append(str(exc))
          ctx.errors.append(traceback.format_exc())
          ctx.state = PipelineState.ERROR
          self._fire("error", {"message": str(exc)})

      return ctx
  ```

- [ ] **Step 4: Run new tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_orchestrator.py -v
  ```
  Expected: all tests pass including the two new ones.

- [ ] **Step 5: Run full suite**

  Run:
  ```bash
  pytest tests/unit/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add pipeline/orchestrator.py tests/unit/test_orchestrator.py
  git commit -m "feat: Orchestrator gains optional progress_callback, fires at each pipeline stage"
  ```

---

## Task 5: ProgressPanel widget (TDD)

**Files:**
- Create: `ui/widgets/__init__.py`
- Create: `ui/widgets/progress_panel.py`
- Create: `tests/unit/test_tui.py` (initial, extended in later tasks)

- [ ] **Step 1: Create the widgets package**

  Create `ui/widgets/__init__.py` (empty file).

- [ ] **Step 2: Write failing tests for ProgressPanel**

  Create `tests/unit/test_tui.py`:

  ```python
  import pytest

  from textual.widgets import Label, ProgressBar


  @pytest.mark.asyncio
  async def test_progress_panel_set_stage_updates_label():
      from ui.widgets.progress_panel import ProgressPanel
      from textual.app import App, ComposeResult

      class TestApp(App):
          def compose(self) -> ComposeResult:
              yield ProgressPanel(id="progress")

      app = TestApp()
      async with app.run_test(size=(80, 10)) as pilot:
          panel = app.query_one(ProgressPanel)
          panel.set_stage(3, "Scoring jobs")
          await pilot.pause()
          label = app.query_one("#progress-label", Label)
          assert "3" in str(label.renderable)
          assert "Scoring jobs" in str(label.renderable)


  @pytest.mark.asyncio
  async def test_progress_panel_set_error_shows_red_text():
      from ui.widgets.progress_panel import ProgressPanel
      from textual.app import App, ComposeResult

      class TestApp(App):
          def compose(self) -> ComposeResult:
              yield ProgressPanel(id="progress")

      app = TestApp()
      async with app.run_test(size=(80, 10)) as pilot:
          panel = app.query_one(ProgressPanel)
          panel.set_error("Something broke")
          await pilot.pause()
          label = app.query_one("#progress-label", Label)
          content = str(label.renderable)
          assert "Something broke" in content
  ```

- [ ] **Step 3: Run tests to verify they fail**

  Run:
  ```bash
  pytest tests/unit/test_tui.py::test_progress_panel_set_stage_updates_label -v
  ```
  Expected: `ModuleNotFoundError: No module named 'ui.widgets.progress_panel'`

- [ ] **Step 4: Create ui/widgets/progress_panel.py**

  ```python
  from textual.app import ComposeResult
  from textual.widgets import Label, ProgressBar, Static


  class ProgressPanel(Static):
      def compose(self) -> ComposeResult:
          yield Label("Pipeline Progress", id="progress-title")
          yield ProgressBar(total=7, show_percentage=False, id="progress-bar")
          yield Label("Waiting to start...", id="progress-label")

      def set_stage(self, n: int, label: str) -> None:
          self.query_one("#progress-bar", ProgressBar).update(progress=n)
          self.query_one("#progress-label", Label).update(f"[{n}/7] {label}")

      def set_error(self, message: str) -> None:
          self.query_one("#progress-label", Label).update(f"[red]Error: {message}[/red]")
  ```

- [ ] **Step 5: Run tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_tui.py -v
  ```
  Expected: both ProgressPanel tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add ui/widgets/__init__.py ui/widgets/progress_panel.py tests/unit/test_tui.py
  git commit -m "feat: add ProgressPanel widget with set_stage/set_error"
  ```

---

## Task 6: JobsTable and ContactsTable widgets (TDD)

**Files:**
- Create: `ui/widgets/jobs_table.py`
- Create: `ui/widgets/contacts_table.py`
- Modify: `tests/unit/test_tui.py` (append)

- [ ] **Step 1: Write failing tests for JobsTable and ContactsTable**

  Append to `tests/unit/test_tui.py`:

  ```python
  @pytest.mark.asyncio
  async def test_jobs_table_add_job_appends_row():
      from ui.widgets.jobs_table import JobsTable
      from textual.app import App, ComposeResult
      from textual.widgets import DataTable
      from unittest.mock import MagicMock

      class TestApp(App):
          def compose(self) -> ComposeResult:
              yield JobsTable(id="jobs")

      app = TestApp()
      async with app.run_test(size=(120, 20)) as pilot:
          job = MagicMock()
          job.title = "Senior Engineer"
          job.company = "Acme Corp"
          job.fit_score = 8.5
          job.source = "linkedin"

          table = app.query_one(JobsTable)
          table.add_job(job)
          await pilot.pause()

          dt = app.query_one("#jobs-dt", DataTable)
          assert dt.row_count == 1


  @pytest.mark.asyncio
  async def test_contacts_table_add_contact_appends_row():
      from ui.widgets.contacts_table import ContactsTable
      from textual.app import App, ComposeResult
      from textual.widgets import DataTable
      from unittest.mock import MagicMock

      class TestApp(App):
          def compose(self) -> ComposeResult:
              yield ContactsTable(id="contacts")

      app = TestApp()
      async with app.run_test(size=(120, 20)) as pilot:
          contact = MagicMock()
          contact.name = "Jane Smith"
          contact.title = "Engineering Manager"
          contact.company = "Acme Corp"

          table = app.query_one(ContactsTable)
          table.add_contact(contact)
          await pilot.pause()

          dt = app.query_one("#contacts-dt", DataTable)
          assert dt.row_count == 1
  ```

- [ ] **Step 2: Run tests to verify they fail**

  Run:
  ```bash
  pytest tests/unit/test_tui.py::test_jobs_table_add_job_appends_row tests/unit/test_tui.py::test_contacts_table_add_contact_appends_row -v
  ```
  Expected: `ModuleNotFoundError` for both.

- [ ] **Step 3: Create ui/widgets/jobs_table.py**

  ```python
  from textual.app import ComposeResult
  from textual.widgets import DataTable, Static


  class JobsTable(Static):
      def compose(self) -> ComposeResult:
          yield DataTable(id="jobs-dt")

      def on_mount(self) -> None:
          self.query_one("#jobs-dt", DataTable).add_columns(
              "Role", "Company", "Score", "Source"
          )

      def add_job(self, job) -> None:
          dt = self.query_one("#jobs-dt", DataTable)
          score = f"{job.fit_score:.1f}" if job.fit_score is not None else "N/A"
          dt.add_row(job.title[:30], job.company[:20], score, job.source)
  ```

- [ ] **Step 4: Create ui/widgets/contacts_table.py**

  ```python
  from textual.app import ComposeResult
  from textual.widgets import DataTable, Static


  class ContactsTable(Static):
      def compose(self) -> ComposeResult:
          yield DataTable(id="contacts-dt")

      def on_mount(self) -> None:
          self.query_one("#contacts-dt", DataTable).add_columns(
              "Name", "Title", "Company"
          )

      def add_contact(self, contact) -> None:
          dt = self.query_one("#contacts-dt", DataTable)
          dt.add_row(contact.name[:25], contact.title[:25], contact.company[:20])
  ```

- [ ] **Step 5: Run tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_tui.py -v
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add ui/widgets/jobs_table.py ui/widgets/contacts_table.py tests/unit/test_tui.py
  git commit -m "feat: add JobsTable and ContactsTable widgets"
  ```

---

## Task 7: MessagesPanel widget (TDD)

**Files:**
- Create: `ui/widgets/messages_panel.py`
- Modify: `tests/unit/test_tui.py` (append)

- [ ] **Step 1: Write failing test for MessagesPanel**

  Append to `tests/unit/test_tui.py`:

  ```python
  @pytest.mark.asyncio
  async def test_messages_panel_add_message_writes_to_log():
      from ui.widgets.messages_panel import MessagesPanel
      from textual.app import App, ComposeResult
      from textual.widgets import RichLog

      class TestApp(App):
          def compose(self) -> ComposeResult:
              yield MessagesPanel(id="messages")

      app = TestApp()
      async with app.run_test(size=(120, 20)) as pilot:
          panel = app.query_one(MessagesPanel)
          panel.add_message("Hi Jane, I saw your role at Acme Corp...")
          await pilot.pause()
          log = app.query_one("#messages-log", RichLog)
          assert log is not None
  ```

- [ ] **Step 2: Run test to verify it fails**

  Run:
  ```bash
  pytest tests/unit/test_tui.py::test_messages_panel_add_message_writes_to_log -v
  ```
  Expected: `ModuleNotFoundError: No module named 'ui.widgets.messages_panel'`

- [ ] **Step 3: Create ui/widgets/messages_panel.py**

  ```python
  from textual.app import ComposeResult
  from textual.widgets import RichLog, Static


  class MessagesPanel(Static):
      def compose(self) -> ComposeResult:
          yield RichLog(id="messages-log", markup=True, wrap=True)

      def add_message(self, message: str) -> None:
          self.query_one("#messages-log", RichLog).write(message)
  ```

- [ ] **Step 4: Run tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_tui.py -v
  ```
  Expected: all tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add ui/widgets/messages_panel.py tests/unit/test_tui.py
  git commit -m "feat: add MessagesPanel widget"
  ```

---

## Task 8: JobSearchApp TUI (TDD)

**Files:**
- Create: `ui/tui.py`
- Modify: `tests/unit/test_tui.py` (append)

- [ ] **Step 1: Write failing tests for JobSearchApp**

  Append to `tests/unit/test_tui.py`:

  ```python
  def _mock_cfg():
      from unittest.mock import MagicMock
      cfg = MagicMock()
      cfg.logging.level = "INFO"
      cfg.database.host = "localhost"
      cfg.database.port = "5432"
      cfg.database.db = "test"
      cfg.database.user = "test"
      cfg.database.password = "test"
      cfg.anthropic_api_key = "test-key"
      cfg.apify_api_token = "test-token"
      cfg.vibe_api_key = "test-vibe-key"
      cfg.vibe_api_base_url = ""
      cfg.scoring.max_contacts_per_category = 5
      cfg.scoring.contact_score_threshold = 5.0
      cfg.scoring.veteran_score_boost = 1.0
      cfg.scoring.job_score_threshold = 7.0
      cfg.scoring.top_n_jobs = 5
      cfg.search.keywords = ["python"]
      cfg.search.location = "Denver, CO"
      cfg.search.remote = True
      cfg.search.onsite = False
      cfg.search.job_type = "full_time"
      cfg.search.time_window_hours = 48
      return cfg


  @pytest.mark.asyncio
  async def test_job_search_app_mounts_all_panels():
      from ui.tui import JobSearchApp
      from ui.widgets.progress_panel import ProgressPanel
      from ui.widgets.jobs_table import JobsTable
      from ui.widgets.contacts_table import ContactsTable
      from ui.widgets.messages_panel import MessagesPanel

      app = JobSearchApp(cfg=_mock_cfg(), cv_path="test.pdf", keywords=[])
      async with app.run_test(size=(120, 40)) as pilot:
          assert app.query_one(ProgressPanel) is not None
          assert app.query_one(JobsTable) is not None
          assert app.query_one(ContactsTable) is not None
          assert app.query_one(MessagesPanel) is not None


  @pytest.mark.asyncio
  async def test_job_search_app_q_exits():
      from ui.tui import JobSearchApp

      app = JobSearchApp(cfg=_mock_cfg(), cv_path="test.pdf", keywords=[])
      async with app.run_test(size=(120, 40)) as pilot:
          await pilot.press("q")
      # Reaching here means the app exited cleanly
  ```

- [ ] **Step 2: Run tests to verify they fail**

  Run:
  ```bash
  pytest tests/unit/test_tui.py::test_job_search_app_mounts_all_panels tests/unit/test_tui.py::test_job_search_app_q_exits -v
  ```
  Expected: `ModuleNotFoundError: No module named 'ui.tui'`

- [ ] **Step 3: Create ui/tui.py**

  ```python
  import json
  from pathlib import Path

  from textual.app import App, ComposeResult
  from textual.binding import Binding
  from textual.containers import Horizontal, Vertical
  from textual.widgets import Footer

  from ui.widgets.contacts_table import ContactsTable
  from ui.widgets.jobs_table import JobsTable
  from ui.widgets.messages_panel import MessagesPanel
  from ui.widgets.progress_panel import ProgressPanel


  class JobSearchApp(App):
      CSS = """
      Screen {
          layout: grid;
          grid-size: 2;
          grid-rows: 5 1fr 1fr;
      }
      ProgressPanel {
          column-span: 2;
          border: solid $accent;
          padding: 0 1;
      }
      JobsTable {
          border: solid $primary;
      }
      ContactsTable {
          border: solid $primary;
      }
      MessagesPanel {
          column-span: 2;
          border: solid $secondary;
      }
      Footer {
          column-span: 2;
      }
      """

      BINDINGS = [Binding("q", "quit", "Quit")]

      def __init__(self, cfg, cv_path: str, keywords: list):
          super().__init__()
          self._cfg = cfg
          self._cv_path = cv_path
          self._keywords = keywords

      def compose(self) -> ComposeResult:
          yield ProgressPanel(id="progress")
          yield JobsTable(id="jobs")
          yield ContactsTable(id="contacts")
          yield MessagesPanel(id="messages")
          yield Footer()

      def on_mount(self) -> None:
          self.run_worker(self._run_pipeline, exclusive=True)

      def _progress_callback(self, stage: str, data: dict) -> None:
          if stage == "loading_cv":
              self.query_one(ProgressPanel).set_stage(1, "Loading CV...")
          elif stage == "searching":
              self.query_one(ProgressPanel).set_stage(2, "Searching Google & LinkedIn...")
          elif stage == "scoring_jobs":
              top_jobs = data.get("top_jobs", [])
              self.query_one(ProgressPanel).set_stage(3, f"Scored {len(top_jobs)} jobs above threshold")
              for job in top_jobs:
                  self.query_one(JobsTable).add_job(job)
          elif stage == "finding_contacts":
              self.query_one(ProgressPanel).set_stage(4, "Finding contacts...")
          elif stage == "scoring_contacts":
              contacts = data.get("contacts", [])
              self.query_one(ProgressPanel).set_stage(5, f"Found {len(contacts)} contacts")
              for contact in contacts:
                  self.query_one(ContactsTable).add_contact(contact)
          elif stage == "generating_messages":
              messages = data.get("messages", [])
              self.query_one(ProgressPanel).set_stage(6, f"Generated {len(messages)} messages")
              for msg in messages:
                  self.query_one(MessagesPanel).add_message(msg)
          elif stage == "complete":
              self.query_one(ProgressPanel).set_stage(7, "Pipeline complete — press q to exit")
          elif stage == "error":
              self.query_one(ProgressPanel).set_error(data.get("message", "Unknown error"))

      async def _run_pipeline(self) -> None:
          from contacts.clients import ApifyContactClient, VibeProspectingClient
          from contacts.finder import ContactFinder
          from cv.loader import CVLoader
          from cv.parser import CVParser
          from db.connection import create_pool, ensure_schema
          from db.repositories.contact_repo import ContactRepository
          from db.repositories.job_repo import JobRepository
          from llm.claude import ClaudeClient
          from messaging.generator import MessageGenerator
          from pipeline.combiner import combine_jobs
          from pipeline.orchestrator import Orchestrator
          from scoring.contact_scorer import ContactScorer
          from scoring.job_scorer import JobScorer
          from search.filters import SearchFilters
          from search.google import GoogleJobSearcher
          from search.linkedin import LinkedInJobSearcher
          from ui.renderer import UIRenderer
          from utils.logger import configure_logging

          cfg = self._cfg
          try:
              configure_logging(level=cfg.logging.level)
          except Exception:
              configure_logging()

          pool = await create_pool(
              host=cfg.database.host,
              port=int(cfg.database.port),
              db=cfg.database.db,
              user=cfg.database.user,
              password=cfg.database.password,
          )
          await ensure_schema(pool)

          llm = ClaudeClient(api_key=cfg.anthropic_api_key)
          apify_contacts = ApifyContactClient(api_token=cfg.apify_api_token)
          vibe_client = VibeProspectingClient(
              api_key=cfg.vibe_api_key, base_url=cfg.vibe_api_base_url
          )
          orch = Orchestrator(
              cv_loader=CVLoader(),
              cv_parser=CVParser(llm=llm),
              google_searcher=GoogleJobSearcher(llm=llm),
              linkedin_searcher=LinkedInJobSearcher(api_token=cfg.apify_api_token),
              combiner=combine_jobs,
              job_scorer=JobScorer(llm=llm),
              contact_finder=ContactFinder(
                  apify_client=apify_contacts,
                  vibe_client=vibe_client,
                  max_per_category=cfg.scoring.max_contacts_per_category,
              ),
              contact_scorer=ContactScorer(
                  threshold=cfg.scoring.contact_score_threshold,
                  veteran_boost=cfg.scoring.veteran_score_boost,
              ),
              message_generator=MessageGenerator(llm=llm),
              job_repo=JobRepository(pool=pool),
              contact_repo=ContactRepository(pool=pool),
              renderer=UIRenderer(),
              job_threshold=cfg.scoring.job_score_threshold,
              contact_threshold=cfg.scoring.contact_score_threshold,
              top_n=cfg.scoring.top_n_jobs,
              progress_callback=self._progress_callback,
          )
          filters = SearchFilters(
              keywords=self._keywords or cfg.search.keywords,
              location=cfg.search.location,
              remote=cfg.search.remote,
              onsite=cfg.search.onsite,
              job_type=cfg.search.job_type,
              time_window_hours=cfg.search.time_window_hours,
          )
          ctx = await orch.run(cv_path=self._cv_path, filters=filters)
          await pool.close()

          if ctx.output:
              Path("output.json").write_text(ctx.output)
  ```

- [ ] **Step 4: Run tests to verify they pass**

  Run:
  ```bash
  pytest tests/unit/test_tui.py::test_job_search_app_mounts_all_panels tests/unit/test_tui.py::test_job_search_app_q_exits -v
  ```
  Expected: both pass.

- [ ] **Step 5: Run full test suite**

  Run:
  ```bash
  pytest tests/unit/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 6: Commit**

  ```bash
  git add ui/tui.py tests/unit/test_tui.py
  git commit -m "feat: add JobSearchApp Textual TUI with 4-panel layout and progress_callback wiring"
  ```

---

## Task 9: CLI integration

**Files:**
- Modify: `cli.py`

Wire `JobSearchApp` into `cli.py` so that `python cli.py full --cv ...` launches the TUI. `run_full()` is retained for programmatic use.

- [ ] **Step 1: Add JobSearchApp import and update main() in cli.py**

  Add this import near the top of `cli.py` with the other imports:
  ```python
  from ui.tui import JobSearchApp
  ```

  Replace the `if args.mode == "full":` block in `main()`:

  ```python
  if args.mode == "full":
      with initialize(config_path="config", version_base=None):
          cfg = compose(config_name="config")
      app = JobSearchApp(cfg=cfg, cv_path=args.cv, keywords=args.keywords)
      app.run()
  ```

  Note: the `with initialize(...)` block must wrap **both** the `compose(config_name="config")` call and any subsequent usage of `cfg`. Move it so `cfg` is available before constructing `JobSearchApp`. The current `main()` already has `with initialize(...)` — update the body of that block:

  ```python
  def main():
      parser = argparse.ArgumentParser(description="Job Search Agent")
      parser.add_argument(
          "mode", choices=["search", "full", "contacts-only"], help="Pipeline mode"
      )
      parser.add_argument("--cv", required=True, help="Path to resume PDF")
      parser.add_argument("--keywords", nargs="*", default=[], help="Search keywords")
      args = parser.parse_args()

      with initialize(config_path="config", version_base=None):
          cfg = compose(config_name="config")

      if args.mode == "full":
          app = JobSearchApp(cfg=cfg, cv_path=args.cv, keywords=args.keywords)
          app.run()
      else:
          logger.info(f"Mode '{args.mode}' not yet implemented — use 'full'")
  ```

- [ ] **Step 2: Run full unit suite to confirm nothing broke**

  Run:
  ```bash
  pytest tests/unit/ -v
  ```
  Expected: all tests pass.

- [ ] **Step 3: Commit**

  ```bash
  git add cli.py
  git commit -m "feat: cli.py full mode launches JobSearchApp TUI"
  ```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Contact discovery: `VibeProspectingClient.find_people()` (Task 2)
- [x] `ContactFinder.find()` uses Vibe directly, Apify path removed (Task 3)
- [x] `ApifyContactClient` stays in constructor signature (Task 3, `_make_finder` keeps it)
- [x] Config: `vibe_api_base_url` in `api_keys.yaml` and `.env` (Task 1)
- [x] `progress_callback` optional on Orchestrator (Task 4)
- [x] Existing Orchestrator tests unchanged (callback defaults to None)
- [x] ProgressPanel with ProgressBar + stage label (Task 5)
- [x] JobsTable DataTable (Task 6)
- [x] ContactsTable DataTable (Task 6)
- [x] MessagesPanel RichLog (Task 7)
- [x] JobSearchApp 2×2 layout (Task 8)
- [x] `q` binding exits app (Task 8)
- [x] Pipeline errors shown in red in ProgressPanel (Task 8 — `error` stage)
- [x] A2UI output.json written on complete (Task 8 — `ctx.output` written to file)
- [x] CLI integration (Task 9)
- [x] `run_full()` retained unchanged (only `main()` modified in Task 9)

**Out of scope (per spec):**
- Google search fix — deferred
- `time_window_hours` config change — deferred
- Vibe email enrichment — not included
- Multi-page Vibe results — not included
- TUI keyboard navigation between panels — not included
