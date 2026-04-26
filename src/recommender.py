"""
Music recommender core — scoring and ranking logic.

Unchanged from the Module 3 show project, with logging added so the
agentic pipeline can observe every scoring decision.
"""

import csv
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class Song:
    """Represents a song and its audio/metadata attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """Represents a user's taste preferences for recommendations."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


class Recommender:
    """OOP wrapper around the scoring and ranking logic."""

    def __init__(self, songs: List[Song]):
        self.songs = songs
        logger.debug("Recommender initialised with %d songs", len(songs))

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs sorted by score for the given user profile."""
        prefs = {
            "genre":  user.favorite_genre,
            "mood":   user.favorite_mood,
            "energy": user.target_energy,
        }
        song_dicts = [
            {
                "id":           s.id,
                "title":        s.title,
                "artist":       s.artist,
                "genre":        s.genre,
                "mood":         s.mood,
                "energy":       s.energy,
                "tempo_bpm":    s.tempo_bpm,
                "valence":      s.valence,
                "danceability": s.danceability,
                "acousticness": s.acousticness,
            }
            for s in self.songs
        ]
        results = recommend_songs(prefs, song_dicts, k=k)
        ranked_titles = [r[0]["title"] for r in results]
        return sorted(
            self.songs,
            key=lambda s: ranked_titles.index(s.title) if s.title in ranked_titles else 999,
        )[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended."""
        prefs = {
            "genre":  user.favorite_genre,
            "mood":   user.favorite_mood,
            "energy": user.target_energy,
        }
        song_dict = {"genre": song.genre, "mood": song.mood, "energy": song.energy}
        _, reasons = score_song(prefs, song_dict)
        return "; ".join(reasons) if reasons else "No strong match found"


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return a list of dicts with numeric fields converted."""
    songs = []
    try:
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                songs.append({
                    "id":           int(row["id"]),
                    "title":        row["title"],
                    "artist":       row["artist"],
                    "genre":        row["genre"],
                    "mood":         row["mood"],
                    "energy":       float(row["energy"]),
                    "tempo_bpm":    float(row["tempo_bpm"]),
                    "valence":      float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                })
    except FileNotFoundError:
        logger.error("Catalog not found: %s", csv_path)
        raise
    logger.info("Loaded %d songs from %s", len(songs), csv_path)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song against user preferences and return (score, reasons).

    Scoring recipe:
      +2.0  genre match        (highest weight — mismatch is immediately audible)
      +1.0  mood match
      +proximity for energy   (1.0 - abs(song_energy - target_energy))
    """
    score = 0.0
    reasons: List[str] = []

    # EXPERIMENT — weight shift: genre 2.0 → 1.0, energy multiplier 1.0 → 2.0
    weight_shift = False
    genre_weight      = 1.0 if weight_shift else 2.0
    energy_multiplier = 2.0 if weight_shift else 1.0

    if song.get("genre") == user_prefs.get("genre"):
        score += genre_weight
        reasons.append(f"genre match (+{genre_weight})")

    if song.get("mood") == user_prefs.get("mood"):
        score += 1.0
        reasons.append("mood match (+1.0)")

    target_energy = user_prefs.get("energy", 0.5)
    song_energy   = song.get("energy", 0.5)
    energy_score  = round((1.0 - abs(song_energy - target_energy)) * energy_multiplier, 3)
    score += energy_score
    reasons.append(
        f"energy proximity ({song_energy:.2f} vs target {target_energy:.2f}, +{energy_score:.2f})"
    )

    logger.debug(
        "score_song: '%s' → %.3f  (%s)",
        song.get("title", "?"),
        round(score, 3),
        " | ".join(reasons),
    )
    return round(score, 3), reasons


def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, str]]:
    """Score every song, rank by score descending, and return the top-k results."""
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, " | ".join(reasons)))

    ranked = sorted(scored, key=lambda item: item[1], reverse=True)
    logger.debug(
        "recommend_songs: top result = '%s' (%.3f)",
        ranked[0][0]["title"] if ranked else "none",
        ranked[0][1] if ranked else 0,
    )
    return ranked[:k]
