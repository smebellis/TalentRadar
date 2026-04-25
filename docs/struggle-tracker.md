# Struggle Tracker

Updated after every passing test and every completed module. Struggled concepts appear first.

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
| `sorted()` with lambda key functions | 🔴 Struggled | — |
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

<!-- Add new entries below as we progress through the build -->
