"""
CLI entry point — Music Recommender (Applied AI System Project).

Two modes:
  agent   (default) — describe a vibe in plain English, get a curated
                       narrative playlist powered by the Gemini agent.
  direct            — supply genre/mood/energy directly and get ranked
                       results with scores (preserves Module 3 behaviour).

Run from the project root:
    python -m src.cli                  # agent mode, interactive
    python -m src.cli --mode direct    # direct scoring mode
"""

import argparse
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

from src.recommender import load_songs, recommend_songs

# ------------------------------------------------------------------
# Logging — writes to stdout AND to recommender.log
# ------------------------------------------------------------------

def _configure_logging() -> None:
    fmt = "%(asctime)s %(levelname)-8s %(name)s — %(message)s"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("recommender.log", encoding="utf-8"),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

CATALOG = "data/songs.csv"


# ------------------------------------------------------------------
# Agent mode
# ------------------------------------------------------------------

def run_agent_mode() -> None:
    """Interactive loop: user types a vibe, agent returns a playlist."""
    try:
        from src.agent import PlaylistAgent
        agent = PlaylistAgent(catalog_path=CATALOG)
    except RuntimeError as exc:
        print(f"\nCannot start agent mode: {exc}")
        print("Set GEMINI_API_KEY in your .env file and try again.\n")
        return

    print("\nPlaylist Curator — Agent Mode")
    print("================================")
    print("Describe a vibe or scenario and the agent will curate a playlist.")
    print("Type 'quit' or press Enter on an empty line to exit.\n")

    while True:
        try:
            vibe = input("Your vibe: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not vibe or vibe.lower() == "quit":
            print("Goodbye.")
            break

        print("\nCurating your playlist...\n")
        try:
            narrative = agent.curate(vibe)
            print("-" * 60)
            print(narrative)
            print("-" * 60)
        except Exception as exc:
            logger.error("Agent error: %s", exc)
            print(f"Something went wrong: {exc}")
        print()


# ------------------------------------------------------------------
# Direct mode
# ------------------------------------------------------------------

def run_direct_mode() -> None:
    """Score-based recommendations using explicit genre/mood/energy inputs."""
    songs = load_songs(CATALOG)

    print("\nDirect Recommender Mode")
    print("========================")
    print("Enter your preferences below (press Enter to use the default).\n")

    genre  = input("Genre  (e.g. lofi, rock, pop): ").strip() or "pop"
    mood   = input("Mood   (e.g. chill, happy, sad): ").strip() or "happy"
    energy_str = input("Energy (0.0–1.0, e.g. 0.4): ").strip() or "0.5"
    k_str  = input("How many songs? (default 5): ").strip() or "5"

    try:
        energy = max(0.0, min(1.0, float(energy_str)))
    except ValueError:
        print("Invalid energy value — using 0.5")
        energy = 0.5

    try:
        k = max(1, int(k_str))
    except ValueError:
        k = 5

    prefs = {"genre": genre, "mood": mood, "energy": energy}
    print(f"\nProfile: genre={genre}  mood={mood}  energy={energy:.2f}\n")

    results = recommend_songs(prefs, songs, k=k)

    print("=" * 62)
    for rank, (song, score, explanation) in enumerate(results, start=1):
        print(f"#{rank}  {song['title']} — {song['artist']}")
        print(f"    Genre: {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']}")
        print(f"    Score: {score:.3f}")
        print(f"    Why:   {explanation}")
        print()


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main() -> None:
    _configure_logging()
    logger.info("CLI started")

    parser = argparse.ArgumentParser(
        description="Music Recommender — Applied AI System Project"
    )
    parser.add_argument(
        "--mode",
        choices=["agent", "direct"],
        default="agent",
        help="'agent' for conversational playlist curation (default), "
             "'direct' for score-based recommendations.",
    )
    args = parser.parse_args()

    if args.mode == "agent":
        run_agent_mode()
    else:
        run_direct_mode()

    logger.info("CLI exited")


if __name__ == "__main__":
    main()
