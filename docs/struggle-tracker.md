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

<!-- Add new entries below as we progress through the build -->
