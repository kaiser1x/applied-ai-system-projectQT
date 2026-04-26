"""
Playlist Curator Agent — Music Recommender (Applied AI System Project).

Agentic workflow (three steps):

  1. Plan    — Gemini reads the user's free-text vibe description and
               returns a structured music profile (genre, mood, energy).

  2. Act     — Python runs the existing recommend_songs() scoring function
               against the local catalog using that profile.
               No LLM is involved in the scoring math.

  3. Narrate — Gemini receives the ranked songs and writes a narrative
               playlist: opening hook, per-song transitions, mood arc.
"""

import json
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from google import genai

from src.recommender import load_songs, recommend_songs

load_dotenv()
logger = logging.getLogger(__name__)

MODEL = "gemini-2.5-flash"

# Catalog values kept in sync with songs.csv so Gemini picks valid options.
VALID_GENRES = [
    "pop", "lofi", "rock", "ambient", "jazz", "synthwave", "indie pop",
    "hip-hop", "r&b", "classical", "electronic", "folk", "metal", "country", "blues",
]
VALID_MOODS = [
    "happy", "chill", "intense", "relaxed", "moody", "focused", "energetic",
    "sad", "nostalgic", "euphoric", "melancholic", "upbeat", "romantic", "angry",
]

# ------------------------------------------------------------------
# Step 1 prompt — extracts a structured profile from free text
# ------------------------------------------------------------------

PLAN_PROMPT = """\
You are a music taste interpreter.

A user will describe a vibe, scenario, or feeling. Your job is to translate \
that into a music profile by choosing values from the lists below.

Available genres : {genres}
Available moods  : {moods}
Energy scale     : 0.0 (very calm/ambient) → 1.0 (very intense/loud)
  0.0–0.3 = ambient / sleep / deep focus
  0.3–0.5 = moderate / background / study
  0.5–0.7 = upbeat / social / walking
  0.7–1.0 = intense / workout / party

Respond with ONLY a JSON object — no extra text:
{{"genre": "<genre>", "mood": "<mood>", "energy": <float 0.0–1.0>}}

User vibe: {vibe}
"""

# ------------------------------------------------------------------
# Step 3 prompt — writes the narrative playlist
# ------------------------------------------------------------------

NARRATE_PROMPT = """\
You are a music curator writing a short playlist narrative for a listener.

The listener described their vibe as: "{vibe}"

The recommender system selected these songs (ranked by match score):
{song_list}

Write a narrative playlist (150–250 words) with:
- An opening hook (1–2 sentences) explaining why this playlist fits the vibe.
- For each song: its title and artist, followed by one sentence on how it \
fits and — for every song after the first — how it transitions from the \
previous track.
- A closing note (1 sentence) on the overall mood arc.

Only reference songs from the list above. Do not invent tracks.
"""


class PlaylistAgent:
    """
    Two-call agentic playlist curator powered by Gemini.

    Usage:
        agent = PlaylistAgent()
        print(agent.curate("something moody for a late-night drive"))
    """

    def __init__(
        self,
        catalog_path: str = "data/songs.csv",
        api_key: Optional[str] = None,
    ) -> None:
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Add it to your .env file to enable the playlist agent."
            )
        self.client = genai.Client(api_key=key)
        self.songs = load_songs(catalog_path)
        logger.info(
            "PlaylistAgent ready — %d songs in catalog, model=%s",
            len(self.songs),
            MODEL,
        )

    # ------------------------------------------------------------------
    # Step 1: Plan — extract music profile from free-text vibe
    # ------------------------------------------------------------------

    def _extract_profile(self, vibe: str) -> dict:
        """
        Ask Gemini to interpret the vibe and return a music profile dict.
        Falls back to sensible defaults if the response cannot be parsed.
        """
        prompt = PLAN_PROMPT.format(
            genres=", ".join(VALID_GENRES),
            moods=", ".join(VALID_MOODS),
            vibe=vibe,
        )

        response = self.client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        raw = response.text.strip()
        logger.debug("Plan step raw response: %s", raw)

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            profile = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Could not parse profile JSON, using defaults. Raw: %s", raw)
            profile = {"genre": "pop", "mood": "happy", "energy": 0.5}

        # Guardrails: ensure values are valid
        if profile.get("genre") not in VALID_GENRES:
            logger.warning("Invalid genre %r — defaulting to 'pop'", profile.get("genre"))
            profile["genre"] = "pop"
        if profile.get("mood") not in VALID_MOODS:
            logger.warning("Invalid mood %r — defaulting to 'relaxed'", profile.get("mood"))
            profile["mood"] = "relaxed"
        try:
            profile["energy"] = max(0.0, min(1.0, float(profile["energy"])))
        except (TypeError, ValueError):
            logger.warning("Invalid energy value — defaulting to 0.5")
            profile["energy"] = 0.5

        logger.info("Profile extracted: %s", profile)
        return profile

    # ------------------------------------------------------------------
    # Step 2: Act — run the existing recommender (no LLM)
    # ------------------------------------------------------------------

    def _get_songs(self, profile: dict, k: int = 5) -> list:
        """Run recommend_songs() and return the ranked results."""
        results = recommend_songs(profile, self.songs, k=k)
        logger.info(
            "Recommender returned %d songs for profile %s", len(results), profile
        )
        return results

    # ------------------------------------------------------------------
    # Step 3: Narrate — write the playlist story
    # ------------------------------------------------------------------

    def _write_narrative(self, vibe: str, results: list) -> str:
        """Ask Gemini to narrate the playlist using the ranked song list."""
        song_lines = "\n".join(
            f"{i+1}. {s['title']} by {s['artist']} "
            f"(genre: {s['genre']}, mood: {s['mood']}, energy: {s['energy']:.2f}, score: {score:.2f})"
            for i, (s, score, _) in enumerate(results)
        )

        prompt = NARRATE_PROMPT.format(vibe=vibe, song_list=song_lines)

        response = self.client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
        return response.text.strip()

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def curate(self, vibe_description: str, k: int = 5) -> str:
        """
        Turn a free-text vibe description into a narrative playlist.

        Returns the narrative string. Raises RuntimeError only on
        unrecoverable API failures.
        """
        vibe = vibe_description.strip()
        if not vibe:
            return "Please describe the vibe or scenario you want a playlist for."

        logger.info("curate() — vibe: %r", vibe[:80])

        # Step 1: Plan
        profile = self._extract_profile(vibe)

        # Step 2: Act
        results = self._get_songs(profile, k=k)
        if not results:
            return "No songs matched that vibe. Try a different description."

        # Step 3: Narrate
        narrative = self._write_narrative(vibe, results)
        logger.info("Narrative generated (%d chars)", len(narrative))
        return narrative
