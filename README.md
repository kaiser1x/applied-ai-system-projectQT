# Music Recommender — Applied AI System Project

## Original Project

This project is an evolution of the **Music Recommendation Simulator** built in Module 3.

The original system was a content-based recommender that scored songs against a user taste profile using weighted feature matching (genre, mood, energy). It operated on a 20-song catalog and ran entirely through hardcoded profiles in a CLI script — no natural language input, no AI generation, no web interface. Its goal was to simulate how real recommenders turn structured data into ranked suggestions, while exposing the biases that emerge from manual weight design.

---

## What This System Does

The final project extends that recommender into a two-mode AI application:

- **Agent mode** — A user describes a vibe in plain English ("something moody for a late-night drive"). A Gemini LLM interprets the description, selects matching song criteria, and the Python scoring engine ranks the catalog. Gemini then writes a narrative playlist with transitions and a mood arc.
- **Direct mode** — The original score-based recommender, now accessible through a web UI with dropdowns and sliders.

The key upgrade is the **agentic workflow**: the LLM plans (extracts criteria), Python acts (runs the scoring math), and the LLM narrates (explains the playlist). The AI actively changes what the system returns — it is not decorative.

---

## Architecture

```
User input (free-text vibe)
         │
         ▼
┌─────────────────────────┐
│  Step 1 — Plan          │  Gemini reads the vibe and returns
│  agent._extract_profile │  a structured profile: genre, mood, energy
└──────────┬──────────────┘
           │ {genre, mood, energy}
           ▼
┌─────────────────────────┐
│  Step 2 — Act           │  Python-only: no LLM involved.
│  recommend_songs()      │  Scores every song in songs.csv against
│  score_song()           │  the profile and returns top-k ranked results.
└──────────┬──────────────┘
           │ ranked song list
           ▼
┌─────────────────────────┐
│  Step 3 — Narrate       │  Gemini receives the actual songs and
│  agent._write_narrative │  writes a playlist narrative with transitions.
└──────────┬──────────────┘
           │ narrative text
           ▼
    Streamlit web UI  /  CLI output
```

Data flows linearly. The LLM never touches the scoring formula — it only sees inputs and outputs. This keeps the scoring layer deterministic and testable.

---

## Setup Instructions

**1. Clone the repo**
```bash
git clone https://github.com/kaiser1x/applied-ai-system-projectQT.git
cd applied-ai-system-projectQT
```

**2. Create a virtual environment (recommended)**
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Mac / Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your Gemini API key**
```bash
cp .env.example .env
```
Open `.env` and replace `your_api_key_here` with your real key.

**5. Run the web app**
```bash
streamlit run app.py
```
The browser opens automatically at `http://localhost:8501`.

**6. Or run from the terminal**
```bash
python -m src.cli               # agent mode (describe a vibe)
python -m src.cli --mode direct # direct scoring mode
```

**7. Run tests**
```bash
pytest
```

---

## Sample Interactions

### Agent mode — vibe: "something to hype me up before a workout"

**Extracted profile:** `genre=electronic, mood=energetic, energy=0.92`

**Narrative output:**
> This playlist is pure fuel — high-energy, bass-heavy, and built to push you past your limits. We open with **Neon Pulse by Gridlock**, a driving electronic track at 0.95 energy that sets the tempo immediately. From there, **Iron Gates by Voltline** shifts the tone to metal — same intensity, harder edge, keeping the adrenaline moving. **Block Party by Crate Kings** brings hip-hop momentum mid-set, a slight drop in energy that feels like controlled breathing before the final push. **Gym Hero by Max Pulse** closes the loop — pop-adjacent but relentlessly upbeat, the kind of track that makes the last set feel easy.

---

### Agent mode — vibe: "late night studying, nothing too distracting"

**Extracted profile:** `genre=lofi, mood=focused, energy=0.38`

**Narrative output:**
> This playlist is designed to disappear into the background — present enough to keep you moving, quiet enough to let you think. **Focus Flow by LoRoom** opens things up: lofi, focused, and steady at 0.40 energy. **Midnight Coding by LoRoom** follows naturally, a step slower but equally grounded. **Library Rain by Paper Lanterns** deepens the mood — acoustic, gentle, built for long stretches. **Spacewalk Thoughts by Orbit Bloom** drifts in at the end, ambient and weightless, the kind of track that makes 2 AM feel manageable.

---

### Direct mode — genre: jazz, mood: relaxed, energy: 0.4

| # | Title | Artist | Score |
|---|---|---|---|
| 1 | Coffee Shop Stories | Slow Stereo | 3.37 |
| 2 | Sunday Porch | June Roads | 2.96 |
| 3 | Library Rain | Paper Lanterns | 2.75 |
| 4 | Blue Note Alley | Slow Stereo | 2.64 |
| 5 | Midnight Coding | LoRoom | 2.62 |

---

## Design Decisions

**Why two LLM calls instead of one?**
Splitting plan and narrate into separate calls keeps each prompt focused and short. A single prompt asking Gemini to "interpret the vibe AND write the playlist" produces lower-quality narratives because the model splits attention. Two focused calls are more reliable.

**Why keep scoring in Python?**
The scoring formula is deterministic, auditable, and testable. If it lived inside a prompt, its behaviour would vary with every call and we could not write unit tests for it. Separating LLM reasoning from algorithmic scoring is a core reliability design principle.

**Why Gemini instead of a fine-tuned model?**
The catalog is only 20 songs — too small to fine-tune on. A general-purpose LLM with a well-designed prompt generalises better to novel vibe descriptions than a model trained on a tiny fixed dataset.

**Trade-offs made:**
- Genre dominance bias (from Module 3) is preserved intentionally — it is documented, not hidden.
- The catalog is small (20 songs), so some vibes return imperfect matches. This is acknowledged in the UI.
- Energy scoring treats "too quiet" and "too loud" as equally bad, which does not match real listener preferences.

---

## Testing Summary

**25 automated tests across two files:**

| Category | Tests | Result |
|---|---|---|
| Recommender correctness | 11 | All pass |
| Determinism | 2 | All pass |
| Scoring correctness | 4 | All pass |
| Edge cases | 6 | All pass |
| Ranking consistency | 2 | All pass |

**Key findings:**
- The scoring function is fully deterministic — identical inputs always produce identical outputs.
- An unknown genre (not in the catalog) does not crash the system; it falls back to mood + energy scoring.
- A k value larger than the catalog size returns all available songs without error.
- All 20 catalog songs have energy values in the valid 0.0–1.0 range.

**What didn't work at first:**
- Gemini occasionally wraps JSON in markdown code fences (` ```json `). A stripping guardrail was added to `_extract_profile()` to handle this.
- A vibe like "classical angry" hits a real catalog gap — no song matches both genre and mood. The system returns the best available options and the narrative acknowledges the mismatch rather than pretending otherwise.

---

## Reflection and Ethics

**Limitations and biases:**
The genre-dominance bias from Module 3 is still present: a genre match (+2.0) can outweigh a perfect mood and energy match combined. A user asking for "sad electronic" may get a happy electronic track over a sad folk track because the genre bonus dominates. The catalog is also small and English-language-centric, so moods expressed in other cultural contexts may not map cleanly to the available labels.

**Could this be misused?**
A music recommender poses low misuse risk, but edge cases exist: if mood detection were added (inferring emotional state from text), the system could surface content to vulnerable users that reinforces negative feelings. Guardrails would include explicit mood escalation detection and a refusal to recommend "sad" or "angry" content when distress signals are present.

**What surprised me during testing:**
Gemini's profile extraction is more robust than expected for ambiguous vibes. "Vibes are immaculate rn" correctly maps to `mood=happy, energy=0.75`. What failed surprisingly was over-literal vibe descriptions — "I want something with guitar" does not map to any catalog feature because `acousticness` and `genre` are the closest proxies and the model sometimes picks `folk` when the user meant `rock`.

**AI collaboration:**
One helpful suggestion: when asked to review the scoring formula, the AI correctly identified that symmetric energy scoring (treating "too quiet" and "too loud" identically) is a known weakness in real-world recommenders and suggested asymmetric weighting as an improvement — a real insight backed by industry literature.

One flawed suggestion: the AI initially recommended using `pandas` to load the CSV for "better performance." For a 20-row file, this adds a dependency with no measurable benefit. The `csv` module from the standard library is the right tool here, and that is what the code uses.
