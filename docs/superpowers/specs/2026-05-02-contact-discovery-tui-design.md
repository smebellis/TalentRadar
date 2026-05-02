# Contact Discovery & TUI Design
**Date:** 2026-05-02
**Status:** Approved

---

## 1. Overview

Two features added to the existing job search pipeline:

1. **Contact Discovery** — Replace the broken Apify LinkedIn people-search path with direct Vibe Prospecting (Explorium) REST API calls. No LinkedIn cookies required.
2. **Textual TUI** — A live, interactive 2×2 terminal dashboard that updates in real-time as each pipeline stage completes. Replaces raw JSON stdout output. A2UI JSON is still written to `output.json`.

---

## 2. Architecture & Data Flow

```
cli.py  ─── JobSearchApp (Textual)
                │
                ├── runs Orchestrator as async worker
                │       │
                │       └── fires progress_callback(stage, data) at each step
                │
                ├── ProgressPanel   ← stage callbacks
                ├── JobsTable       ← jobs callback (fires after scoring)
                ├── ContactsTable   ← contacts callback (fires after finding)
                └── MessagesPanel   ← messages callback (fires after generation)

                On complete → writes output.json (A2UI JSON)
                Stays open → user presses q to exit
```

Contact discovery change is isolated to `VibeProspectingClient` and `ContactFinder`:

```
VibeProspectingClient
  ├── find_people(company, job_title) → list[dict]   ← NEW
  └── enrich(people)                                  ← existing (unchanged)

ContactFinder.find(job)
  ├── calls vibe_client.find_people() directly        ← changed
  └── falls back to [] + warning if unconfigured      ← graceful
```

The `Orchestrator` gains one optional parameter: `progress_callback: Callable | None = None`. When set, it fires at each stage with the stage name and data produced. When `None`, behavior is identical to today — all existing tests pass unmodified.

---

## 3. Contact Discovery

### VibeProspectingClient changes

Add `find_people()` method:

```python
def find_people(self, company: str, job_title: str, max_results: int = 20) -> list[dict]
```

- **Implementation note:** The exact endpoint path, auth header format, request body shape, and response field names must be verified against the Explorium REST API docs (or by making a live test call) before coding. The MCP tool schema (`fetch-entities`) suggests searching by company may require a two-step flow: first resolve the company to a `business_id`, then fetch prospects filtered by that ID. Do not guess the field names.
- Returns `[]` (with WARNING log) if `base_url` is unset, on HTTP error, or on 402 (credits exhausted)
- The output dict shape that `ContactFinder` expects is fixed regardless of API field names:
  ```python
  {
    "name": str,
    "title": str,
    "company": str,        # always the job.company value passed in
    "linkedin_url": str,
    "email": str | None,
    "notes": str           # <100 chars, e.g. location
  }
  ```

### ContactFinder changes

- Remove Apify client dependency from `find()` — call `vibe_client.find_people(company, job_title)` directly
- `ApifyContactClient` parameter stays in the constructor signature for now (avoids breaking caller) but is ignored in `find()`

### Environment & Config

Add to `.env`:
```
VIBE_API_BASE_URL=https://api.explorium.ai/v1
```

Add to `config/api_keys.yaml`:
```yaml
vibe_api_base_url: ${oc.env:VIBE_API_BASE_URL,}
```

Pass `base_url=cfg.vibe_api_base_url` when constructing `VibeProspectingClient` in `cli.py`.

---

## 4. Textual TUI

### Layout

```
┌─────────────────────────────────────────┐
│  Pipeline Progress          [stage/7]   │
│  ████████░░░░░░░░  [3/7] Scoring jobs   │
├───────────────────────┬─────────────────┤
│  Jobs (3 found)       │  Contacts (0)   │
│  Role  Co  Score  Src │  Name  Title    │
│  ...                  │  ...            │
├───────────────────────┴─────────────────┤
│  Outreach Messages                      │
│  [Vail Resorts — Jane Smith]            │
│  Hi Jane, I noticed your role at...     │
└─────────────────────────────────────────┘
 Pipeline complete — press q to exit
```

### Files

| File | Purpose |
|---|---|
| `ui/tui.py` | `JobSearchApp(App)` — Textual app, layout, worker, callback wiring |
| `ui/widgets/progress_panel.py` | `ProgressPanel` widget — progress bar + stage label |
| `ui/widgets/jobs_table.py` | `JobsTable` widget — scrollable DataTable for jobs |
| `ui/widgets/contacts_table.py` | `ContactsTable` widget — scrollable DataTable for contacts |
| `ui/widgets/messages_panel.py` | `MessagesPanel` widget — scrollable RichLog for outreach messages |

### Key Design Decisions

- **Event loop ownership:** Textual's `App` owns the asyncio event loop. The orchestrator runs inside it as `run_worker(exclusive=True)` — no separate `asyncio.run()`.
- **Progress callback:** `progress_callback(stage: str, data: dict)` is the only interface between the orchestrator and TUI. The orchestrator imports nothing from `ui/`.
- **Reactive updates:** Each widget exposes a method (e.g., `add_job(job)`, `set_stage(n, label)`) called from the worker via `self.app.call_from_thread()`.
- **Quit:** Binding `q` → `app.exit()`. Footer shows `Pipeline complete — press q to exit` on completion.
- **Error display:** Pipeline errors appear in red in the progress panel. App stays open so the user can read partial results.
- **A2UI output:** Written to `output.json` in the working directory when pipeline completes. Not printed to stdout.

### cli.py integration

```python
if args.mode == "full":
    app = JobSearchApp(cfg=cfg, cv_path=args.cv, keywords=args.keywords)
    app.run()
```

`run_full()` is retained as-is for non-TUI / programmatic use.

---

## 5. Testing

### New test files

| File | Coverage |
|---|---|
| `tests/unit/test_vibe_client.py` | `find_people()` maps response correctly; returns `[]` when base_url unset; returns `[]` on HTTP error; returns `[]` on 402 |
| `tests/unit/test_contact_finder.py` (extend) | `find()` calls `vibe_client.find_people()`; Apify path no longer invoked |
| `tests/unit/test_tui.py` | App mounts all 4 panels; `progress_callback` updates panel data; `q` exits app |

### Existing tests

No changes required. `Orchestrator(progress_callback=None)` is the default — all current tests pass unmodified.

---

## 6. Out of Scope

- Google search fix (deferred)
- `time_window_hours` change (deferred — separate config-only change)
- Vibe Prospecting email enrichment (free tier may not support it)
- Multi-page / paginated Vibe results
- TUI keyboard navigation between panels
