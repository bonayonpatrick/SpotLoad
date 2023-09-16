import requests
import ytm
from youtubesearchpython import VideosSearch

from . import spotify
from .utils import retry_on_fail, concat_comma, choose_items


def choose_from_youtube(query, duration=0, delta=3, auto=False):
    results = VideosSearch(query, limit=20).result().get("result")

    _items = {}
    for result in results:
        duration_spl = result.get("duration").split(":")
        minutes, seconds = int(duration_spl[0]), int(duration_spl[1])
        total_sec = (minutes * 60) + seconds

        # calculate delta to match the closest result
        if ((abs(total_sec - duration) < delta) or duration == 0) and result["type"] == "video":
            result["duration"] = total_sec
            _items[f"{result.get('channel').get('name')} - {result['title']}"] = result

    def _prefix_action(_video_id):
        return _video_id

    video_id, index = choose_items(
        title=f"Choose Audio from YouTube",
        items=list(_items.keys()),
        auto_select=auto,
        prefix="id#",
        callback=_prefix_action,
    )

    return video_id or list(_items.values())[index]["id"]


def choose_from_youtube_music(query, duration=0, delta=3, auto=False):
    api = ytm.YouTubeMusic()
    items = api.search_songs(query)["items"]

    _items = {}
    try:
        for item in items:
            artist = concat_comma([artist['name'] for artist in item['artists']])
            # calculate delta to match the closest result
            if (abs(item['duration'] - duration) < delta) or duration == 0:
                _items[f"{artist} - {item['name']}"] = item
    except TypeError:
        return choose_from_youtube_music(query, duration, delta, auto)

    def _prefix_action(video_id):
        if result := api.song(video_id):
            return result
        print("invalid video id")

    video: dict
    video, index = choose_items(
        title=f"Choose Audio from YouTube Music",
        items=list(_items.keys()),
        prefix="id#",
        callback=_prefix_action,
        auto_select=auto
    )

    video = video or list(_items.values())[index]

    return {
        "id": video["id"],
        "duration": video["duration"],
        "metadata": {
            "title": video["name"],
            "artist": [artist["name"] for artist in video["artists"]],
            "album": video["album"]["name"]
        }
    }


def choose_from_spotify(query, auto=False):
    tracks = spotify.search(q=query)["tracks"]

    _items = {}
    for item in tracks["items"]:
        if item['type'] == "track":
            song_name = item["name"]
            artist = concat_comma([artist["name"] for artist in item["artists"]])

            _items[f"{artist} - {song_name}"] = item

    def _prefix_action(track_id):
        if result := spotify.track(track_id=track_id):
            return result
        print("invalid track id")

    track: dict
    track, index = choose_items(
        title=f"Choose Metadata",
        items=list(_items.keys()),
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


def search_query(query, auto=True, use_ytm=True):
    if (track := choose_from_spotify(query, auto=auto)) is None:
        return

    metadata = track["metadata"]

    if use_ytm:
        if (video := choose_from_youtube_music(
            f"{concat_comma(metadata['artist'])} - {metadata['title']}",
            duration=track["duration"],
            auto=auto
        )) is None:
            return

        metadata["title"] = video["metadata"]["title"]
        metadata["artist"] = video["metadata"]["artist"]
        video_id = video["id"]
    else:
        if (video_id := choose_from_youtube(
            f"{concat_comma(metadata['artist'])} - {metadata['title']} audio",
            duration=track["duration"],
            auto=auto
        )) is None:
            return

    return track["id"], video_id, metadata
