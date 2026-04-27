# Music Curator — Applied AI System Project

An AI-powered music recommendation web app that turns a free-text vibe description into a curated, narrated playlist. Built with Streamlit, Gemini 2.5 Flash, and a deterministic Python scoring engine.

## Demo

[Watch the demo on Loom](https://www.loom.com/share/49f82991e6934ec4b7d2c6c0abff6fc4)

---

## Original Project

**Original project:** Music Recommender Simulation (Module 3 Show project)

The Module 3 project was a command-line music recommender that scored songs from a 20-song CSV catalog against a structured user profile (genre, mood, energy level). It matched preferences using a weighted scoring formula and returned ranked results with explanations. The system was fully deterministic — no AI was involved in scoring.

This Applied AI project extends that foundation by wrapping it in a three-step agentic loop powered by Gemini 2.5 Flash and delivering results through a polished web interface.

---

## Title and Summary

**Music Curator** lets you describe a feeling or scenario in plain language and builds a soundtrack from it. Most music apps require you to already know what you want — a genre, an artist, a playlist name. Type *"something moody for a late-night drive in the rain"* and the system interprets your vibe, scores every song in the catalog, and writes a narrative playlist that explains why each track fits and how they flow together. The AI handles fuzzy human language; the deterministic scorer handles the ranking math.

---

## Advanced AI Feature: Agentic Workflow

This project implements a **three-step agentic workflow** fully integrated into the main application:

| Step | Who Acts | What Happens |
|------|----------|--------------|
| **Plan** | Gemini 2.5 Flash | Reads the user's free-text vibe and returns a structured music profile: `{genre, mood, energy}` |
| **Act** | Python (`recommender.py`) | Runs `recommend_songs()` against the 20-song catalog using that profile — no LLM involved |
| **Narrate** | Gemini 2.5 Flash | Receives the ranked songs and writes a 150–250 word playlist narrative with transitions and mood arc |

The AI output from Step 1 directly determines which songs are retrieved in Step 2. If Gemini interprets "late-night drive" as `{genre: lofi, mood: chill, energy: 0.3}`, the scoring engine returns a completely different ranking than if it returned `{genre: synthwave, mood: moody, energy: 0.6}`. This is not cosmetic — the agentic loop produces meaningfully different results based on LLM interpretation.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User (Browser)                           │
│               Streamlit Web UI — app.py                         │
│      ┌──────────────────┐   ┌────────────────────────┐         │
│      │  Playlist Curator │   │    Direct Search        │         │
│      │  (Agentic Mode)  │   │  (Filter + Score Mode)  │         │
│      └────────┬─────────┘   └───────────┬────────────┘         │
└───────────────┼───────────────────────────┼─────────────────────┘
                │                           │
                ▼                           ▼
┌──────────────────────────┐   ┌──────────────────────────────┐
│   STEP 1 — PLAN          │   │   Direct Score               │
│   PlaylistAgent          │   │   recommend_songs()          │
│   Gemini 2.5 Flash       │   │   (genre + mood + energy     │
│                          │   │    filters applied first)    │
│   Input:  free-text vibe │   └──────────────────────────────┘
│   Output: {genre, mood,  │
│            energy} JSON  │
└──────────────┬───────────┘
               │ structured profile
               ▼
┌──────────────────────────┐
│   STEP 2 — ACT           │
│   recommend_songs()      │   ← Deterministic Python, no LLM
│   src/recommender.py     │
│                          │
│   Scores all 20 songs:   │
│     +2.0 genre match     │
│     +1.0 mood match      │
│     +proximity energy    │
│   Returns top-5 ranked   │
└──────────────┬───────────┘
               │ [(song, score, reasons), ...]
               ▼
┌──────────────────────────┐
│   STEP 3 — NARRATE       │
│   PlaylistAgent          │
│   Gemini 2.5 Flash       │
│                          │
│   Input:  ranked songs   │
│   Output: narrative text │
│   (150–250 words)        │
└──────────────┬───────────┘
               │
               ▼
        ┌─────────────┐       ┌────────────────────────┐
        │  Song Cards │       │   Automated Test Suite  │
        │  + Narrative│       │   pytest — 24 tests     │
        │  Displayed  │       │   tests/test_*.py       │
        └─────────────┘       └────────────────────────┘
```

**Data flow:** User text → Gemini interprets vibe → Python scores catalog → Gemini narrates results → UI displays ranked song cards with match scores, mood badges, energy bars, and per-song explanations.

---

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- A [Google AI Studio](https://aistudio.google.com/) API key (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/kaiser1x/applied-ai-system-projectQT.git
cd applied-ai-system-projectQT
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure your API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

### 4. Run the app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### 5. Run tests (optional, no API key needed)

```bash
pytest tests/ -v
```

---

## Sample Interactions

### Example 1 — Agentic Mode: Late-Night Vibe

**Input:** `"something moody for a late-night drive in the rain"`

**AI Profile extracted (Step 1):**
```json
{"genre": "lofi", "mood": "melancholic", "energy": 0.3}
```

**Top Results from scorer (Step 2):**

| Rank | Song | Match Score |
|------|------|-------------|
| 1 | Midnight Reverie | 3.85 |
| 2 | Rain on Glass | 3.72 |
| 3 | Hollow Hours | 3.61 |

**Narrative written by Gemini (Step 3):**
> *"This playlist was built for the quiet hours — the kind where streetlights blur in the wet windshield and your thoughts move slower than traffic. We open with Midnight Reverie, a lofi piece that settles into the stillness without demanding your attention. It dissolves into Rain on Glass, a track that carries the same low-energy melancholy but introduces a gentle rhythmic pulse — like windshield wipers keeping time. Hollow Hours closes the arc, leaning further into introspection. The overall mood here is one of comfortable solitude: present, unhurried, and just melancholic enough to feel honest."*

---

### Example 2 — Agentic Mode: Focused Morning

**Input:** `"focused morning study session"`

**AI Profile extracted (Step 1):**
```json
{"genre": "electronic", "mood": "focused", "energy": 0.55}
```

**Top Results from scorer (Step 2):**

| Rank | Song | Match Score |
|------|------|-------------|
| 1 | Grid Lock | 3.90 |
| 2 | Signal Path | 3.74 |
| 3 | Morning Protocol | 3.60 |

**Narrative written by Gemini (Step 3):**
> *"These tracks are engineered for clarity — background energy that sharpens focus without pulling attention away from the work. Grid Lock opens with a steady electronic pulse that signals the brain to shift into a productive state. Signal Path follows with a slightly warmer texture, bridging the mechanical and the human. Morning Protocol rounds out the set with a measured rhythm that carries through the final stretch of a study block. The arc moves from activation to sustained attention."*

---

### Example 3 — Direct Search Mode

**Filters applied:** Genre = `synthwave`, Mood = `nostalgic`, Energy slider = `0.6`

**Result:** 5 songs returned instantly with numeric match scores, energy bars, mood-color badges, and expandable "Why this song?" explanations — no AI call, fully deterministic, sub-100ms response.

---

## Design Decisions and Trade-offs

**Hybrid architecture (LLM + deterministic scorer):** The AI interprets fuzzy human language; Python handles the scoring math. This keeps recommendations transparent, testable, and consistent — and means all 24 tests run without ever calling the Gemini API.

**Gemini 2.5 Flash over a larger model:** Speed matters in a web app. Flash responses arrive in 1–3 seconds. The trade-off is occasionally less nuanced profile extraction for unusual or abstract vibes, which the guardrail system catches.

**20-song catalog:** Kept small intentionally so scoring behavior is fully observable and tests can assert exact results. A production system would integrate with the Spotify API or a larger dataset.

**Two modes (Agentic vs. Direct):** Users who already know their preferences should not be forced through an AI roundtrip. Direct Search applies filters immediately and returns results without any LLM call.

**Guardrails over failure:** If Gemini returns an invalid genre or mood, the agent falls back to safe defaults (`pop`, `relaxed`, `0.5`) and logs a warning rather than crashing or returning garbage recommendations. All LLM output is validated against the catalog's known value lists before it touches the scorer.

---

## Reliability and Evaluation: Testing Summary

```
24 tests — 24 passed, 0 failed
Run: pytest tests/ -v
```

**test_recommender.py (10 tests)** — core recommender behavior:
- Correct result count for any `k`
- Top result matches genre and mood for a perfect preference profile
- Genre match always scores higher than no genre match
- Full match (genre + mood) always beats partial match (genre only)
- Energy proximity scoring: closer energy = higher score
- Score type is always `float`
- Output is sorted descending by score
- Empty catalog returns empty list, no crash
- Input song list is not mutated by the ranking function

**test_reliability.py (14 tests)** — reliability, determinism, edge cases:
- `score_song` is deterministic: 5 consecutive identical calls return identical results
- `recommend_songs` ranking is deterministic across runs
- Perfect match scores higher than worst-case mismatch
- Energy proximity is symmetric: `+0.2` above target = `+0.2` below target
- Score is always `>= 0` for any input combination
- `k` larger than catalog returns all songs without crash
- Unknown genre (not in catalog) does not crash — returns results with no genre bonus
- Reasons list is always non-empty for any scored song
- CSV catalog loads with exactly 20 songs with all required fields
- All catalog energy values are in `[0.0, 1.0]`

**What worked:** Deterministic scorer behaved exactly as designed across all cases. Guardrails caught 100% of the invalid Gemini outputs encountered during manual testing (moods like `"peaceful"` and `"dreamy"` that were not in the catalog list).

**What didn't:** Tie-breaking when multiple songs have identical scores is handled by Python's stable sort (first-encountered wins). This is deterministic but not semantically meaningful — a secondary sort criterion like `valence` would produce more musically coherent tie-breaks.

**Confidence scores:** Every song card displays a numeric match score (`0.0 – 4.0`). A score below `1.5` means no genre or mood match occurred — only energy proximity contributed. This gives users a transparent signal of recommendation confidence.

---

## Reflection: What This Taught Me About AI and Problem-Solving

Building this system made the boundary between "AI does it" and "code does it" concrete. The temptation is to let the LLM handle everything — but that makes results untestable and unpredictable. Splitting responsibilities (LLM for interpretation, Python for scoring) meant I could write 24 tests without ever calling the Gemini API, and I could trust the ranking math completely.

The biggest insight: **AI is best used at the edges of structured systems** — where human language needs to be converted into machine-readable input, or where machine output needs to be converted back into human-readable narrative. The middle layer (scoring and ranking) should stay deterministic and testable.

---

## Limitations and Biases

**Catalog bias:** The 20-song catalog was hand-authored and reflects a limited genre vocabulary. Genres like bossanova, Afrobeats, or K-pop are absent entirely. Users who describe vibes outside this vocabulary get fallback defaults that may feel irrelevant.

**Genre weight dominance:** Genre match adds `+2.0` points; mood only adds `+1.0`. A song can rank first by matching genre alone even if its mood is completely wrong. This makes genre the dominant signal, which may not match every listener's actual preference hierarchy.

**Gemini consistency:** The Plan step is non-deterministic — the same vibe description may produce slightly different profiles across runs, leading to different rankings. The guardrail catches invalid values but cannot catch valid-but-wrong interpretations (e.g., `jazz` when the user clearly wanted `lofi`).

**No user feedback loop:** The system has no memory of past sessions and cannot learn from user corrections or ratings over time.

---

## Could This AI Be Misused?

The primary risk is prompt injection through the vibe text field — a user could attempt to override the system prompt and get Gemini to return data outside the music domain. The current guardrail validates Gemini's output against an explicit allowlist of genres and moods and falls back to defaults if any value is invalid. Extending this to sanitize the raw input (e.g., reject inputs over 500 characters or flag injection patterns) would be the next defensive step. The system poses no significant societal harm risk given its narrow music-recommendation scope.

---

## What Surprised Me During Testing

The determinism tests were the most revealing. I assumed the scoring math was "obviously" deterministic — but had not considered that sort stability matters when scores tie. Testing this explicitly caught the assumption rather than leaving it as invisible technical debt.

The Gemini guardrails were also triggered more frequently than expected. Early testing showed Gemini returning moods like `"peaceful"` or `"dreamy"` that were not in the catalog's mood list. Without the validation step, those would have silently produced zero mood-match scores for every song, degrading recommendation quality invisibly.

---

## Collaboration With AI During This Project

**Helpful suggestion:** The AI assistant suggested splitting the agentic loop into three separately callable methods (`_extract_profile`, `_get_songs`, `_write_narrative`) rather than one monolithic `curate()` call. This made it possible to cache each step's result in `st.session_state` independently, so a page interaction (like clicking a chip preset) would not re-run the expensive Gemini API calls unnecessarily. This was a non-obvious architectural improvement that meaningfully changed the app's performance.

**Flawed suggestion:** The AI assistant repeatedly suggested using CSS `display: none !important` on Streamlit's header element to hide the default UI chrome. This worked visually but hid the sidebar's collapse/reopen control as an unintended side effect — the control is a child of the same header container, so hiding the parent made it inaccessible. It took several rounds of debugging to identify this as the root cause of the sidebar becoming unrecoverable after collapsing. The correct fix was to use JavaScript to hide only the specific bad child elements individually, leaving the container — and the sidebar toggle — intact.
