import requests

from .. import spotify
from ..utils import smart_join, retry_on_fail, choose_items


def choose_from_spotify(query, auto=False):
    tracks = spotify.search(q=query)["tracks"]

    _items = {}
    for item in tracks["items"]:
        if item['type'] == "track":
            song_name = item["name"]
            artist = smart_join([artist["name"] for artist in item["artists"]])

            _items[f"{artist} - {song_name}"] = item

    def _prefix_action(track_id):
        if result := spotify.track(track_id=track_id):
            return result
        print("invalid track id")

    track, index = choose_items(
        # title=f"[{tracks['limit']}/{tracks['total']}] Choose Metadata",
        title=f"Choose Metadata",
        items=_items.keys(),
        prefix="id#",
        callback=_prefix_action,
        auto_select=auto
    )

    track = track or list(_items.values())[index]

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
        "album_art": lambda: retry_on_fail(lambda: requests.get(track["album"]["images"][0]["url"]).content),
        "genre": lambda: spotify.artist(track["artists"][0]["external_urls"]["spotify"])["genres"]
    }

    release_date = track["album"]["release_date"]

    if len(dates := release_date.split("-")) == 3:
        audio_metadata["year"] = dates[0]
    else:
        audio_metadata["original_date"] = release_date
        audio_metadata["date"] = release_date

    metadata["metadata"] = audio_metadata

    return metadata
