"""
Reliability tests — Music Recommender (Applied AI System Project).

These tests verify that the recommender system behaves consistently and
handles edge cases safely. They do NOT call the Gemini API — only the
deterministic Python scoring layer is tested here.

Run with: pytest tests/test_reliability.py -v
"""

import pytest
from src.recommender import score_song, recommend_songs, load_songs


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def make_song(title="Song", genre="pop", mood="happy", energy=0.5):
    return {
        "id": 1, "title": title, "artist": "Test", "genre": genre,
        "mood": mood, "energy": energy, "tempo_bpm": 120,
        "valence": 0.5, "danceability": 0.5, "acousticness": 0.3,
    }


CATALOG_PATH = "data/songs.csv"


# ------------------------------------------------------------------
# Determinism — same input must always produce the same output
# ------------------------------------------------------------------

class TestDeterminism:
    def test_score_song_is_deterministic(self):
        prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4}
        song  = make_song(genre="lofi", mood="chill", energy=0.4)
        scores = [score_song(prefs, song)[0] for _ in range(5)]
        assert len(set(scores)) == 1, "score_song must return the same value on repeated calls"

    def test_recommend_songs_is_deterministic(self):
        songs = [
            make_song("A", genre="pop",  mood="happy",   energy=0.8),
            make_song("B", genre="lofi", mood="chill",   energy=0.4),
            make_song("C", genre="rock", mood="intense", energy=0.9),
        ]
        prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
        run1 = [s["title"] for s, _, _ in recommend_songs(prefs, songs, k=3)]
        run2 = [s["title"] for s, _, _ in recommend_songs(prefs, songs, k=3)]
        assert run1 == run2, "recommend_songs must produce the same ranking on repeated calls"


# ------------------------------------------------------------------
# Scoring correctness
# ------------------------------------------------------------------

class TestScoringCorrectness:
    def test_perfect_match_scores_higher_than_no_match(self):
        prefs      = {"genre": "jazz", "mood": "relaxed", "energy": 0.4}
        perfect    = make_song(genre="jazz",  mood="relaxed", energy=0.4)
        no_match   = make_song(genre="metal", mood="angry",   energy=0.95)
        p_score, _ = score_song(prefs, perfect)
        n_score, _ = score_song(prefs, no_match)
        assert p_score > n_score

    def test_genre_match_contributes_positively(self):
        prefs      = {"genre": "blues", "mood": "sad", "energy": 0.4}
        with_genre = make_song(genre="blues", mood="happy", energy=0.5)
        no_genre   = make_song(genre="pop",   mood="happy", energy=0.5)
        w_score, _ = score_song(prefs, with_genre)
        n_score, _ = score_song(prefs, no_genre)
        assert w_score > n_score

    def test_energy_proximity_is_symmetric(self):
        prefs  = {"genre": "ambient", "mood": "chill", "energy": 0.5}
        above  = make_song(genre="ambient", mood="chill", energy=0.7)
        below  = make_song(genre="ambient", mood="chill", energy=0.3)
        a_score, _ = score_song(prefs, above)
        b_score, _ = score_song(prefs, below)
        # Both are 0.2 away — scores must be equal
        assert abs(a_score - b_score) < 1e-9, (
            "Energy proximity should treat equal distances identically"
        )

    def test_score_is_non_negative_for_any_song(self):
        """Scores should always be >= 0 (energy proximity is always positive)."""
        prefs = {"genre": "metal", "mood": "angry", "energy": 1.0}
        song  = make_song(genre="classical", mood="nostalgic", energy=0.0)
        score, _ = score_song(prefs, song)
        assert score >= 0


# ------------------------------------------------------------------
# Edge cases and guardrails
# ------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_catalog_returns_empty_list(self):
        prefs   = {"genre": "pop", "mood": "happy", "energy": 0.8}
        results = recommend_songs(prefs, [], k=5)
        assert results == []

    def test_k_larger_than_catalog_returns_all(self):
        songs = [make_song(f"Song{i}") for i in range(3)]
        prefs = {"genre": "pop", "mood": "happy", "energy": 0.5}
        results = recommend_songs(prefs, songs, k=100)
        assert len(results) == 3

    def test_unknown_genre_does_not_crash(self):
        """A genre not in the catalog should still produce ranked results."""
        songs = [make_song(genre="pop"), make_song(genre="lofi")]
        prefs = {"genre": "bossanova", "mood": "relaxed", "energy": 0.4}
        results = recommend_songs(prefs, songs, k=2)
        assert len(results) == 2  # returns results even with no genre match

    def test_score_reasons_list_is_non_empty(self):
        prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
        song  = make_song(genre="pop", mood="happy", energy=0.8)
        _, reasons = score_song(prefs, song)
        assert len(reasons) > 0

    def test_catalog_loads_from_csv(self):
        songs = load_songs(CATALOG_PATH)
        assert len(songs) == 20
        required_keys = {"id", "title", "artist", "genre", "mood", "energy"}
        for song in songs:
            assert required_keys.issubset(song.keys())

    def test_catalog_energy_values_in_range(self):
        songs = load_songs(CATALOG_PATH)
        for song in songs:
            assert 0.0 <= song["energy"] <= 1.0, (
                f"Energy out of range for '{song['title']}': {song['energy']}"
            )


# ------------------------------------------------------------------
# Ranking consistency
# ------------------------------------------------------------------

class TestRankingConsistency:
    def test_top_result_is_best_scorer(self):
        songs = [
            make_song("Best",  genre="hip-hop", mood="energetic", energy=0.85),
            make_song("Worse", genre="folk",    mood="melancholic", energy=0.3),
        ]
        prefs   = {"genre": "hip-hop", "mood": "energetic", "energy": 0.85}
        results = recommend_songs(prefs, songs, k=2)
        assert results[0][0]["title"] == "Best"
        assert results[0][1] >= results[1][1]

    def test_recommendations_are_sorted_descending(self):
        songs = [make_song(f"Song{i}", energy=i * 0.1) for i in range(10)]
        prefs = {"genre": "pop", "mood": "happy", "energy": 0.5}
        results = recommend_songs(prefs, songs, k=5)
        scores = [score for _, score, _ in results]
        assert scores == sorted(scores, reverse=True)
