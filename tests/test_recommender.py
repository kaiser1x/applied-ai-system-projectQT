"""
Tests for the core recommender — ported from the Module 3 starter and expanded.
"""

from src.recommender import Song, UserProfile, Recommender, score_song, recommend_songs


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

def make_small_catalog() -> list:
    return [
        Song(id=1, title="Test Pop Track", artist="Test Artist",
             genre="pop", mood="happy", energy=0.8, tempo_bpm=120,
             valence=0.9, danceability=0.8, acousticness=0.2),
        Song(id=2, title="Chill Lofi Loop", artist="Test Artist",
             genre="lofi", mood="chill", energy=0.4, tempo_bpm=80,
             valence=0.6, danceability=0.5, acousticness=0.9),
        Song(id=3, title="Intense Rock Anthem", artist="Test Artist",
             genre="rock", mood="intense", energy=0.95, tempo_bpm=160,
             valence=0.3, danceability=0.6, acousticness=0.05),
    ]


def make_recommender() -> Recommender:
    return Recommender(make_small_catalog())


# ------------------------------------------------------------------
# Recommender class tests (from starter)
# ------------------------------------------------------------------

def test_recommend_returns_correct_count():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_recommender()
    results = rec.recommend(user, k=2)
    assert len(results) == 2


def test_recommend_top_result_matches_genre():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_recommender()
    results = rec.recommend(user, k=3)
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_non_empty():
    user = UserProfile(favorite_genre="pop", favorite_mood="happy",
                       target_energy=0.8, likes_acoustic=False)
    rec = make_recommender()
    explanation = rec.explain_recommendation(user, rec.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ------------------------------------------------------------------
# score_song unit tests
# ------------------------------------------------------------------

def test_score_song_genre_match_adds_points():
    prefs = {"genre": "pop", "mood": "sad", "energy": 0.5}
    song  = {"genre": "pop", "mood": "happy", "energy": 0.5}
    score, reasons = score_song(prefs, song)
    assert score > 0
    assert any("genre match" in r for r in reasons)


def test_score_song_full_match_beats_partial():
    prefs = {"genre": "lofi", "mood": "chill", "energy": 0.4}
    full    = {"genre": "lofi", "mood": "chill",  "energy": 0.4}
    partial = {"genre": "lofi", "mood": "intense", "energy": 0.4}
    full_score, _    = score_song(prefs, full)
    partial_score, _ = score_song(prefs, partial)
    assert full_score > partial_score


def test_score_song_energy_proximity():
    prefs   = {"genre": "pop", "mood": "happy", "energy": 0.5}
    close   = {"genre": "rock", "mood": "sad", "energy": 0.5}   # exact energy
    distant = {"genre": "rock", "mood": "sad", "energy": 0.0}   # far energy
    close_score, _   = score_song(prefs, close)
    distant_score, _ = score_song(prefs, distant)
    assert close_score > distant_score


def test_score_song_returns_float():
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    song  = {"genre": "pop", "mood": "happy", "energy": 0.8}
    score, _ = score_song(prefs, song)
    assert isinstance(score, float)


# ------------------------------------------------------------------
# recommend_songs function tests
# ------------------------------------------------------------------

def test_recommend_songs_respects_k():
    songs = [
        {"id": i, "title": f"Song {i}", "artist": "A", "genre": "pop",
         "mood": "happy", "energy": 0.5, "tempo_bpm": 120,
         "valence": 0.5, "danceability": 0.5, "acousticness": 0.2}
        for i in range(10)
    ]
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.5}
    results = recommend_songs(prefs, songs, k=3)
    assert len(results) == 3


def test_recommend_songs_sorted_descending():
    songs = [
        {"id": 1, "title": "Full Match",  "artist": "A", "genre": "rock",
         "mood": "intense", "energy": 0.9, "tempo_bpm": 150,
         "valence": 0.4, "danceability": 0.6, "acousticness": 0.05},
        {"id": 2, "title": "No Match",    "artist": "B", "genre": "lofi",
         "mood": "chill",   "energy": 0.3, "tempo_bpm": 70,
         "valence": 0.7, "danceability": 0.5, "acousticness": 0.9},
    ]
    prefs   = {"genre": "rock", "mood": "intense", "energy": 0.9}
    results = recommend_songs(prefs, songs, k=2)
    assert results[0][0]["title"] == "Full Match"
    assert results[0][1] > results[1][1]


def test_recommend_songs_empty_catalog():
    results = recommend_songs({"genre": "pop", "mood": "happy", "energy": 0.5}, [], k=5)
    assert results == []


def test_recommend_songs_does_not_mutate_input():
    songs = [
        {"id": 1, "title": "A", "artist": "X", "genre": "pop",
         "mood": "happy", "energy": 0.8, "tempo_bpm": 120,
         "valence": 0.8, "danceability": 0.8, "acousticness": 0.1},
        {"id": 2, "title": "B", "artist": "Y", "genre": "rock",
         "mood": "intense", "energy": 0.9, "tempo_bpm": 160,
         "valence": 0.3, "danceability": 0.6, "acousticness": 0.05},
    ]
    original_order = [s["id"] for s in songs]
    recommend_songs({"genre": "pop", "mood": "happy", "energy": 0.8}, songs, k=2)
    assert [s["id"] for s in songs] == original_order
