# Model Card — Music Curator

## Model Details

| Field | Value |
|-------|-------|
| **Model used** | Gemini 2.5 Flash (Google AI Studio) |
| **Access method** | Google Generative AI Python SDK (`google-generativeai`) |
| **Application** | Music Curator — Applied AI System Project |
| **Tasks** | (1) Vibe-to-profile extraction, (2) Playlist narrative generation |

---

## Intended Use

Music Curator uses Gemini 2.5 Flash in two specific steps of a three-step agentic workflow:

- **Step 1 — Plan:** Converts a user's free-text vibe description (e.g., *"something moody for a late-night drive in the rain"*) into a structured music profile `{genre, mood, energy}` that a deterministic Python scorer can consume.
- **Step 3 — Narrate:** Receives the top-5 ranked songs and writes a 150–250 word playlist narrative explaining the mood arc, transitions, and why each track fits.

The middle layer (Step 2 — scoring and ranking) is fully deterministic Python with no LLM involvement.

**Intended users:** Students, music listeners, and developers exploring agentic AI workflows.
**Intended environment:** Local development and educational demos.

---

## Model Selection Rationale

Gemini 2.5 Flash was chosen over larger models (e.g., Gemini 1.5 Pro) for two reasons:

1. **Speed:** Flash responses arrive in 1–3 seconds, which matters in a web UI where the user is waiting.
2. **Cost:** The free tier on Google AI Studio is sufficient for development and demo use.

The trade-off is occasionally less nuanced profile extraction for unusual or abstract vibes — mitigated by the guardrail system that validates all LLM output against an explicit allowlist before it reaches the scorer.

---

## How the Model Is Used

### Step 1 — Profile Extraction

The model receives a system prompt instructing it to return only a JSON object with three fields: `genre`, `mood`, and `energy`. The user's raw vibe text is passed as the user message. Output is validated against known catalog values before use.

**Example input:** `"chill Sunday morning with coffee"`
**Example output:** `{"genre": "lofi", "mood": "relaxed", "energy": 0.35}`

### Step 3 — Narrative Generation

The model receives the top-5 ranked songs (title, genre, mood, energy, match score) and is instructed to write a 150–250 word narrative that describes the playlist's mood arc and transitions in natural language.

---

## Guardrails and Validation

All Gemini output passes through a validation layer before touching the scorer:

- `genre` must be in the catalog's known genre list; otherwise defaults to `"pop"`
- `mood` must be in the catalog's known mood list; otherwise defaults to `"relaxed"`
- `energy` must be a float in `[0.0, 1.0]`; otherwise defaults to `0.5`

During manual testing, Gemini returned out-of-vocabulary moods (`"peaceful"`, `"dreamy"`) more frequently than expected. The guardrail caught 100% of these cases and substituted safe defaults rather than crashing or silently degrading recommendations.

---

## Limitations and Biases

**Catalog bias:** The 20-song catalog was hand-authored and reflects a limited genre vocabulary. Genres like bossanova, Afrobeats, and K-pop are absent. Users who describe vibes outside this vocabulary receive fallback defaults that may feel irrelevant.

**Genre weight dominance:** Genre match adds `+2.0` to a song's score; mood adds only `+1.0`. A song can rank first by matching genre alone even if its mood is wrong. This makes genre the dominant signal, which may not match every listener's actual preference hierarchy.

**LLM non-determinism:** The Plan step is non-deterministic — the same vibe description may produce slightly different profiles across runs, producing different rankings. The guardrail catches invalid values but cannot catch valid-but-wrong interpretations (e.g., `jazz` when the user clearly intended `lofi`).

**No feedback loop:** The system has no memory of past sessions and cannot improve from user corrections or ratings over time.

**Prompt injection risk:** A user could attempt to override the system prompt via the vibe text field. Current mitigation: output validation against an explicit allowlist. Future improvement: input sanitization (length cap, injection pattern detection).

---

## Evaluation and Testing

The deterministic scoring layer is covered by 24 automated tests (run with `pytest tests/ -v`, no API key required). The LLM steps are evaluated through manual testing only — no automated evaluation of Gemini output quality is currently in place.

| Test Suite | Tests | Covers |
|------------|-------|--------|
| `test_recommender.py` | 10 | Core scoring correctness |
| `test_reliability.py` | 14 | Determinism, edge cases, catalog integrity |

---

## Reflections

### What this project taught me about AI

Building this system made the boundary between "AI does it" and "code does it" concrete. The temptation is to let the LLM handle everything — but that makes results untestable and unpredictable. Splitting responsibilities (LLM for interpretation, Python for scoring) meant I could write 24 tests without ever calling the Gemini API, and I could trust the ranking math completely.

**Core insight: AI is best used at the edges of structured systems** — where human language needs to be converted into machine-readable input, or where machine output needs to be converted back into human-readable narrative. The middle layer should stay deterministic and testable.

### What surprised me

The determinism tests were the most revealing. I assumed the scoring math was "obviously" deterministic — but had not considered that sort stability matters when scores tie. Testing this explicitly caught a hidden assumption rather than leaving it as invisible technical debt.

The guardrails were triggered more frequently than expected. Early testing showed Gemini returning moods like `"peaceful"` or `"dreamy"` that were not in the catalog's mood list. Without validation, those would have silently produced zero mood-match scores for every song, degrading recommendation quality invisibly.

### Collaboration with AI during development

**Helpful suggestion:** The AI assistant suggested splitting the agentic loop into three separately callable methods (`_extract_profile`, `_get_songs`, `_write_narrative`) rather than one monolithic `curate()` call. This made it possible to cache each step's result in `st.session_state` independently, so a page interaction would not re-run expensive Gemini API calls unnecessarily. This was a non-obvious architectural improvement that meaningfully changed the app's performance.

**Flawed suggestion:** The AI assistant repeatedly suggested using CSS `display: none !important` on Streamlit's header element to hide default UI chrome. This worked visually but hid the sidebar's collapse/reopen control as an unintended side effect — the control is a child of the same header container. The correct fix was to use JavaScript to hide only the specific child elements individually, leaving the sidebar toggle intact.

---

## Ethical Considerations

Music Curator operates in a narrow, low-stakes domain (music recommendations) and poses no significant societal harm risk. The primary ethical concern is prompt injection through the vibe text field, addressed by output validation. No personal data is stored or transmitted beyond the active session.
