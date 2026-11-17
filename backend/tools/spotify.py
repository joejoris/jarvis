"""Spotify: opens searches/playback targets — free, no OAuth needed."""
import os
import urllib.parse
from backend import config


def spotify_play(query: str) -> str:
    q = query.strip()
    uri = "spotify:search:" + urllib.parse.quote(q)
    try:
        os.startfile(uri)  # Windows: hands off to the Spotify app
    except Exception:
        import webbrowser
        webbrowser.open("https://open.spotify.com/search/" + urllib.parse.quote(q))
    return f"Opening Spotify for '{q}'."
