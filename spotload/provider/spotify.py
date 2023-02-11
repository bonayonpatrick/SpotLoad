import base64

import requests
from spotipy import Spotify, SpotifyClientCredentials

from spotload.chooser import Chooser
from spotload.utils import smart_join, retry_on_fail

# using spotdl token
spotify = Spotify(auth_manager=SpotifyClientCredentials(
    client_id="5f573c9620494bae87890c0f08a60293",
    client_secret="212476d9b0f3472eaa762d90b19b0ba8"
))


def choose_from_spotify(query, auto=False):
    results = spotify.search(q=query)
    tracks = results["tracks"]

    spotify_chooser = Chooser(f"[{tracks['limit']}/{tracks['total']}] Choose Music from Spotify", auto=auto)

    for item in tracks["items"]:
        if item['type'] == "track":
            song_name = item["name"]
            artist = smart_join([artist["name"] for artist in item["artists"]])

            spotify_chooser.add_item(f"{artist} - {song_name}", item)

    if (track := spotify_chooser.choose()) is None:
        return

    metadata = {
        "id": track["id"],
        "duration": track["duration_ms"] // 1000,
        "popularity": track["popularity"],
    }

    audio_metadata = {
        "album": track["album"]["name"],
        "title": track["name"],
        "artist": [artist["name"] for artist in track["artists"]],
        "track_number": str(track["track_number"]),
        "disc_number": str(track["disc_number"]),
    }

    print("downloading album art...")
    audio_metadata["album_art"] = retry_on_fail(
        lambda: requests.get(track["album"]["images"][0]["url"]).content
    )

    print("fetching album genre...")
    audio_metadata["genre"] = spotify.artist(track["artists"][0]["external_urls"]["spotify"])["genres"]

    release_date = track["album"]["release_date"]

    if len(dates := release_date.split("-")) == 3:
        audio_metadata["year"] = dates[0]
    else:
        audio_metadata["original_date"] = release_date
        audio_metadata["date"] = release_date

    metadata["metadata"] = audio_metadata

    return metadata
