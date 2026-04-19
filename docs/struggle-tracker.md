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
| Import style for mockability | 🟡 Needed a nudge | — |
| Dependency injection pattern | 🟡 Needed a nudge | — |
| Dataclass `field(default_factory=...)` | 🟢 Solid | — |
| Enum for type-safe state | 🟢 Solid | — |
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

<!-- Add new entries below as we progress through the build -->
