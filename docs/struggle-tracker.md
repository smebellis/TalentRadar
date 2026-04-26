# Struggle Tracker

Updated after every passing test and every completed module. Struggled concepts appear first.

---

## Known Tech Debt

| Item | Notes |
|---|---|
| `LinkedInJobSearcher` uses `api_token` internally instead of injected client | Should match `ContactFinder` DI pattern; tests need `patch` removed and `MagicMock()` passed directly |

---

## Legend

| Status | Meaning |
|---|---|
| 🔴 Struggled | Needed multiple hints or direct explanation |
| 🟡 Needed a nudge | Got there with 1-2 guiding questions |
| 🟢 Solid | Implemented correctly with little or no guidance |

---

## Concepts to Watch (carry-over from Take 1)

| Concept | Take 1 Status | Take 2 Status |
|---|---|---|
| Mock ordering (define → patch → create → test) | 🔴 Struggled ×3 | — |
| Class-level vs instance-level attribute access | 🔴 Struggled ×3 | — |
| Wrong data source (raw dict vs scored model) | 🔴 Struggled ×2 | — |
| `sorted()` with lambda key functions | 🔴 Struggled | 🟢 Solid — found lambda key independently after one prompt in Take 2 |
| State value vs context object | 🔴 Struggled | — |
| `os.getenv` timing (`__post_init__`) | 🔴 Struggled | — |
| Import style for mockability | 🟡 Needed a nudge | 🟡 Needed a nudge — understood patch target after one prompt |
| Dependency injection pattern | 🟡 Needed a nudge | — |
| Dataclass `field(default_factory=...)` | 🟢 Solid | 🟢 Solid — implemented cleanly |
| Enum for type-safe state | 🟢 Solid | 🟢 Solid — no issues |
| `json.dumps()` bridge to LLM user messages | 🟢 Solid | — |
| List comprehension filtering | 🟢 Solid | — |
| `enumerate()` for positional indexing | 🟢 Solid | — |

---

## 2026-04-19 — Module: Pydantic Models (Task 4)

| Concept | Status | Notes |
|---|---|---|
| `float \| None = None` optional field syntax | 🔴 Struggled | Took several rounds — confused `Field(default_factory=None)` with simple default |
| `model_validator(mode="after")` | 🟡 Needed a nudge | First time using it; needed guidance on `raise ValueError` vs `return None` and setting `self.field` |
| `Field(default_factory=uuid4)` | 🟢 Solid | Understood why factory vs static default matters |
| `default_factory` vs `default` | 🟢 Solid | Correctly explained shared-instance risk unprompted |
| Pydantic type validation at construction | 🟢 Solid | Understood ValidationError purpose immediately |
| `is_veteran=(category == "veteran")` inline bool | 🟢 Solid | Read it correctly on first explanation |

## 2026-04-20 — Module: PipelineState + Logger + LLM Protocol (Tasks 5–7)

| Concept | Status | Notes |
|---|---|---|
| Python `Protocol` (typing) | 🔴 Struggled | Unfamiliar with the concept; needed explanation before writing tests |
| `logging.getLogger` vs `logging.Logger` | 🟡 Needed a nudge | Implemented with `Logger()` directly; understood registry pattern after one question |
| `patch` for mocking external clients | 🟡 Needed a nudge | Understood MagicMock but needed prompt on where patch goes relative to the test |
| `@runtime_checkable` Protocol + `isinstance` | 🟡 Needed a nudge | Grasped it once shown — used it correctly in test |
| Chained mock attribute setup (`mock.x.y.return_value`) | 🟢 Solid | Set up `mock_messages.create.return_value.content` correctly without hints |
| Enum member values (`{s.value for s in Enum}`) | 🟢 Solid | Understood set comprehension over enum members immediately |
| `dataclass` + `field(default_factory=list)` | 🟢 Solid | Implemented `PipelineContext` cleanly on first attempt |
| Typo discipline (case sensitivity) | 🟡 Needed a nudge | `GENERATE_MESSAGEs` caught after running tests — fixed promptly |

## 2026-04-21 — Module: ClaudeClient Implementation (Task 7)

| Concept | Status | Notes |
|---|---|---|
| `import anthropic` vs `from anthropic import Anthropic` for mockability | 🔴 Struggled | Initially said `from anthropic import Anthropic`; needed multiple rounds to connect import style to patch target |
| SDK call chain (`self.client.messages.create`) | 🔴 Struggled | Kept writing `self.client.create()` — missing `.messages` — across multiple attempts even after direct explanation |
| `api_key` as keyword argument | 🟡 Needed a nudge | Wrote positional first; corrected quickly on first prompt |
| `messages` list shape (`{"role": "user", "content": user}`) | 🟡 Needed a nudge | Set `role` to the `system` variable instead of the literal `"user"` string initially |
| `system` as top-level kwarg to `.create()` | 🟡 Needed a nudge | Asked whether it was a valid parameter before adding it |
| Where to instantiate SDK client (`__init__` vs `complete`) | 🟢 Solid | Correctly chose `__init__` without prompting |
| Extracting `response.content[0].text` | 🟢 Solid | Reasoned through list indexing and `.text` attribute correctly |

## 2026-04-22 — Module: CVLoader (Task 3 Step 5 + Implementation)

| Concept | Status | Notes |
|---|---|---|
| Separation of concerns (loader vs parser) | 🟡 Needed a nudge | Initially thought CVLoader should return a ResumeProfile; one question clarified the two-module split |
| String vs bytes (`get_text()` vs `encode`) | 🟡 Needed a nudge | Had `encode("utf8")` — corrected on first question |
| Accumulating vs overwriting in a loop | 🟡 Needed a nudge | Loop was overwriting `text` each iteration; reasoned through to list comprehension + join |
| `"\n".join([...])` pattern | 🟢 Solid | Reached the list comprehension approach independently after loop issue was identified |

## 2026-04-22 — Module: CVParser (Task 3 Step 6 + Implementation)

| Concept | Status | Notes |
|---|---|---|
| `json.dumps` vs `json.loads` | 🔴 Struggled | Used `dumps` (dict→string) when `loads` (string→dict) was needed; needed direct correction |
| `**data` dict unpacking into Pydantic model | 🔴 Struggled | Tried positional and dot-notation before reaching keyword unpacking |
| LLM call belongs inside `parse`, not a separate method | 🟡 Needed a nudge | Extracted `complete` as a separate CVParser method; redirected with one question |
| `system=` and `user=` as keyword args to `llm.complete` | 🟡 Needed a nudge | Passed positionally first; corrected after looking at test assertion |
| Module-level string constant vs config/env var | 🟡 Needed a nudge | Initially thought SYSTEM_PROMPT was an env var or argument; one question clarified |

## 2026-04-23 — Module: SearchFilters + GoogleJobSearcher (Step 7)

| Concept | Status | Notes |
|---|---|---|
| Time-window filter condition (`job.posted_at > now - timedelta`) | 🔴 Struggled | Blanked on the condition entirely; also confused where `job` variable existed in the loop |
| Hardcoded value vs config field (`48` vs `filters.time_window_hours`) | 🔴 Struggled | Hardcoded 48 twice — once during implementation, once after tests passed |
| Pydantic v2 `model_dump_json()` vs `.json()` | 🟡 Needed a nudge | Knew about `.json()` but needed to be told Pydantic v2 uses `model_dump_json()` |
| Return type: `list` vs single object | 🟡 Needed a nudge | Initially returned a single `Job`; corrected after one question about `len(results)` |
| `source="google"` hardcoded vs reading from LLM response | 🟡 Needed a nudge | Got a KeyError on `source` before realising it should be hardcoded |
| Pydantic BaseModel vs dataclass for SearchFilters | 🟡 Needed a nudge | Said dataclass first; one question redirected to BaseModel |
| `list[str]` type annotation | 🟡 Needed a nudge | Wrote bare `list` without the type parameter |
| `datetime.now(timezone.utc)` for tz-aware comparison | 🟢 Solid | Reached this independently once the comparison was framed |
| Dependency injection (`llm: LLMClient` in `__init__`) | 🟢 Solid | Applied the pattern correctly without prompting |

## 2026-04-24 — Module: LinkedInJobSearcher (Step 8)

| Concept | Status | Notes |
|---|---|---|
| Sync vs async (no `await` in test = sync method) | 🔴 Struggled | Used `ApifyClientAsync` and `async def` — needed two rounds to connect test call style to sync requirement |
| Patch target maps to the file that imports it | 🟡 Needed a nudge | Initially thought `ApifyClient` needed to be imported in `LLMClient`; one question on the patch path resolved it |
| Dataset called on `ApifyClient` instance, not actor | 🟡 Needed a nudge | Called `actor_client.dataset()` first; corrected after tracing mock chain |
| Raw dict → `Job` conversion (architectural rule) | 🟡 Needed a nudge | Returned raw dicts initially; question about test assertion redirected to model construction |
| `_recent_iso()` purpose (time-relative test data) | 🟢 Solid | Correctly explained why hardcoded timestamps would always fail the filter |
| `run["defaultDatasetId"]` from actor run | 🟢 Solid | Traced the mock chain correctly after being guided to it |
| `filters.keywords` / `filters.location` in `run_input` | 🟢 Solid | Spotted the empty `run_input` independently and fixed it without prompting |

## 2026-04-25 — Module: Combiner (Step 9)

| Concept | Status | Notes |
|---|---|---|
| Dict as dedup structure (key → object) | 🟡 Needed a nudge | Started with a set, then a list concat; redirected to dict after one question about retaining the Job object |
| `setdefault` for "insert only if missing" | 🟡 Needed a nudge | Knew the mechanism but initially passed two separate args instead of a tuple key |
| Tuple as composite dict key `(title, company)` | 🟡 Needed a nudge | Wrote `job = (Job.title, Job.company)` — class vs instance and key-vs-assignment confusion; corrected with two prompts |
| `.values()` to extract objects from dict | 🔴 Struggled | Used `list(combined_jobs)` which returns keys; needed direct hint on `.values()` |
| Naming consistency (dict name vs function name) | 🟡 Needed a nudge | Typed `combine_jobs[...]` (function name) when dict was `combined_jobs` — caught by tests |

## 2026-04-25 — Module: JobScorer (Task 3 Step 10 + Implementation)

| Concept | Status | Notes |
|---|---|---|
| Direction of scoring (job scored against resume, not resume scored) | 🟡 Needed a nudge | Initially described it backwards; one question about which model has `fit_score` resolved it |
| JSON object vs array for single-item LLM response | 🟡 Needed a nudge | Said array first; guided to object since one job = one call |
| `list[Job]` parameter vs single `Job` | 🟡 Needed a nudge | Wrote singular `job` then indexed `job[0]`; corrected after one question about parameter name |
| f-string to combine fields into LLM user prompt | 🟡 Needed a nudge | Was building a growing list of tuples across loop iterations; needed direct example to shift to per-iteration f-string |
| `sorted()` with lambda key | 🟢 Solid | Found `key=lambda c: c.fit_score` independently after one prompt — improvement over Take 1 |
| `breakpoint()` left in code | 🔴 Recurring habit | Second occurrence this session; watch for this on every implementation going forward |

## 2026-04-25 — Module: ContactScorer (Step 11)

| Concept | Status | Notes |
|---|---|---|
| `sorted()` with lambda key functions | 🟡 Needed a nudge | Aware it was needed but syntax still uncomfortable — needed a prompt to connect `self.PRIORITIES[item.category]` as the key |
| Class variable as lookup table | 🟡 Needed a nudge | First intentional use; understood immutability tradeoff after one question |
| Double condition guard (searcher AND contact both veteran) | 🟡 Needed a nudge | Initially set `item.is_veteran = True` instead of checking it; corrected after one question |
| `+=` vs `=` for applying a boost | 🟡 Needed a nudge | Used `= self.veteran_boost` (set) instead of `+= self.veteran_boost` (add); caught on first review |
| `breakpoint()` left in code | 🔴 Recurring habit | Third occurrence — must scan for debug statements before every review |
| List comprehension for filtering | 🟢 Solid | Chose it independently and used correct condition |
| Parameter naming (plural vs keyword match) | 🟡 Needed a nudge | `contact` vs `contacts` and `is_veteran` vs `searcher_is_veteran` — caught on signature review |

## 2026-04-26 — Module: ContactFinder (Task 16)

| Concept | Status | Notes |
|---|---|---|
| Dependency injection — where clients come from | 🔴 Struggled | Multiple rounds needed; kept thinking `find` should instantiate or call `.actor()`; needed direct explanation that the injected client is just called |
| External API returns raw dicts, not models | 🔴 Struggled | Initially said `find_people` returns `Contact` objects; needed several questions to land on raw dicts |
| `or` fallback pattern (`enrich(...) or raw_people`) | 🔴 Struggled | Needed direct explanation of how Python `or` evaluates falsy empty list |
| Module-level constants vs class-level | 🟡 Needed a nudge | Good instinct to use a dict mapping; thought it belonged inside the class; one question on `self` dependency resolved it |
| Helper functions at module level | 🟢 Solid | Correctly identified need for `_infer_category` and `_is_veteran_profile` as separate helpers |
| Company filter inside loop (`continue` pattern) | 🟢 Solid | Implemented correctly first try |
| `category_counts` dict for max-per-category guard | 🟢 Solid | Understood the pattern and applied it cleanly |

## 2026-04-26 — Module: Database Repositories (Task 18)

| Concept | Status | Notes |
|---|---|---|
| `MagicMock` vs `AsyncMock` for pool mock | 🔴 Struggled | Knew `pool.acquire()` returns an object (not coroutine), but kept saying `AsyncMock`; needed several rounds to connect that to using `MagicMock` for the pool |
| `__aenter__`/`__aexit__` must be `AsyncMock` | 🟡 Needed a nudge | Once the pool was a `MagicMock`, understood that the async context manager protocol still needs `AsyncMock` for `__aenter__`/`__aexit__` |
| Parameterized queries (`$1, $2, ...`) vs string interpolation | 🟢 Solid | Reached parameterized syntax independently after one prompt on SQL injection |
| `async with self.pool.acquire() as conn:` pattern | 🟢 Solid | Once mock issue was resolved, implemented both repos cleanly |
| `save(contact, job_id)` signature vs `save(job, contact)` | 🟡 Needed a nudge | Swapped argument order and type; caught after comparing test call signature |

## 2026-04-26 — Module: UIRenderer (Task 19)

| Concept | Status | Notes |
|---|---|---|
| A2UI output structure (type, version, tables, summary) | 🔴 Struggled | Unfamiliar with the format; needed to consult the implementation plan to understand top-level keys and table shape |
| Building nested dicts for JSON output | 🔴 Struggled | Needed the plan spec to understand how to structure `job_table`, `contact_table`, and `priority_summary` as nested dicts |
| `json.dumps(..., default=str)` for UUID/datetime serialization | 🟢 Solid | Applied it correctly without prompting |
| List comprehension to build row dicts | 🟢 Solid | Implemented `job_rows` and `contact_rows` cleanly |
| Lookup dict pattern (`{id: value}`) to join messages to contacts | 🟢 Solid | Built `msg_by_contact` independently |

## 2026-04-26 — Module: Orchestrator (Task 20)

| Concept | Status | Notes |
|---|---|---|
| `try/except Exception as e` for pipeline error handling | 🟡 Needed a nudge | Wrote bare `except:` and referenced `PipelineState.ERROR` without setting it; corrected after two questions |
| `ctx = X` vs `ctx.state = X` (overwriting context) | 🔴 Struggled | Wrote `ctx = PipelineState.FINDING_CONTACTS` — overwrote the whole context; needed direct question to spot it |
| `asyncio.gather` result unpacking | 🟢 Solid | Reached tuple unpacking independently |
| `asyncio.to_thread` for sync methods in async context | 🟢 Solid | Applied correctly without prompting |
| `Optional[ResumeProfile]` / `Optional[SearchFilters]` on dataclass | 🟡 Needed a nudge | Used `Optional[Type]` (wrong — means a class) instead of the actual model types |
| Cleaning up unused imports | 🟢 Solid | Identified and removed all unused imports when asked |

<!-- Add new entries below as we progress through the build -->
