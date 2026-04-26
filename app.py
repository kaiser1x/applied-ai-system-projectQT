"""
Streamlit web app — Music Recommender (Applied AI System Project).

Run with:
    streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.recommender import load_songs, recommend_songs

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Music Recommender",
    page_icon="🎵",
    layout="centered",
)

CATALOG = "data/songs.csv"

# ------------------------------------------------------------------
# Sidebar — mode switcher
# ------------------------------------------------------------------

st.sidebar.title("🎵 Music Recommender")
mode = st.sidebar.radio(
    "Mode",
    ["Agent — describe a vibe", "Direct — enter preferences"],
)

# ------------------------------------------------------------------
# Agent mode
# ------------------------------------------------------------------

if mode == "Agent — describe a vibe":
    st.title("Playlist Curator")
    st.write("Describe a vibe or scenario and the AI will curate a playlist for you.")

    vibe = st.text_area(
        "Your vibe",
        placeholder="e.g. something moody for a late-night drive",
        height=80,
    )

    if st.button("Curate Playlist", type="primary"):
        if not vibe.strip():
            st.warning("Please describe a vibe first.")
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                st.error("GEMINI_API_KEY not found. Add it to your .env file.")
            else:
                with st.spinner("Curating your playlist..."):
                    try:
                        from src.agent import PlaylistAgent
                        agent = PlaylistAgent(catalog_path=CATALOG, api_key=api_key)
                        narrative = agent.curate(vibe)
                        st.success("Playlist ready!")
                        st.markdown(narrative)
                    except Exception as exc:
                        st.error(f"Something went wrong: {exc}")

# ------------------------------------------------------------------
# Direct mode
# ------------------------------------------------------------------

else:
    st.title("Direct Recommender")
    st.write("Enter your preferences and see ranked song matches with scores.")

    songs = load_songs(CATALOG)
    genres = sorted(set(s["genre"] for s in songs))
    moods  = sorted(set(s["mood"]  for s in songs))

    col1, col2 = st.columns(2)
    with col1:
        genre = st.selectbox("Genre", genres)
        mood  = st.selectbox("Mood",  moods)
    with col2:
        energy = st.slider("Energy", 0.0, 1.0, 0.5, step=0.05,
                           help="0 = very calm, 1 = very intense")
        k = st.slider("Number of songs", 1, 10, 5)

    if st.button("Get Recommendations", type="primary"):
        prefs   = {"genre": genre, "mood": mood, "energy": energy}
        results = recommend_songs(prefs, songs, k=k)

        st.markdown(f"**Profile:** genre=`{genre}` · mood=`{mood}` · energy=`{energy:.2f}`")
        st.divider()

        for rank, (song, score, explanation) in enumerate(results, start=1):
            with st.container():
                st.markdown(f"**#{rank} — {song['title']}** · *{song['artist']}*")
                cols = st.columns(4)
                cols[0].metric("Genre",  song["genre"])
                cols[1].metric("Mood",   song["mood"])
                cols[2].metric("Energy", f"{song['energy']:.2f}")
                cols[3].metric("Score",  f"{score:.2f}")
                with st.expander("Why this song?"):
                    st.write(explanation)
            st.divider()
