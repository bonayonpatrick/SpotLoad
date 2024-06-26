import requests
from ytmusicapi import YTMusic

from . import spotify
from .utils import retry_on_fail, concat_comma, choose_items, extract_video_id, remove_extra_parentheses


def choose_from_spotify(query, auto=False):
    tracks = spotify.search(q=query)["tracks"]

    _items = {}
    for i, item in enumerate(tracks["items"]):
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
        title=f"Choose Metadata from Spotify:",
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
        "album": remove_extra_parentheses(track["album"]["name"]),
        "title": remove_extra_parentheses(track["name"]),
        "artist": [remove_extra_parentheses(artist["name"]) for artist in track["artists"]],
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


def choose_from_youtube_music(query: str, duration=0, delta=6, auto=False, use_yt=False):
    ytm = YTMusic()
    video_id = None

    if query.startswith("https://"):
        video_id = extract_video_id(query)
        results = ytm.search(video_id)
    else:
        results = ytm.search(query)

    _items = {}
    for result in results:
        if result['resultType'] == ('video' if use_yt else 'song'):
            artist = concat_comma([artist['name'] for artist in result['artists']])

            if video_id and result["videoId"] != video_id:
                continue

            # calculate delta to match the closest result
            if duration == 0 or (abs(result['duration_seconds'] - duration) < delta):
                _items[f"{artist} - {result['title']}"] = result

    video: dict
    video, index = choose_items(
        title=f"Choose Audio from YouTube Music:",
        items=list(_items.keys()),
        auto_select=auto
    )

    video = video or list(_items.values())[index]

    def get_lyrics():
        watch_playlist = ytm.get_watch_playlist(video["videoId"])
        if lyrics_id := watch_playlist.get("lyrics"):
            return ytm.get_lyrics(lyrics_id)["lyrics"]

    metadata = {
        "id": video["videoId"],
        "duration": video["duration_seconds"],
        "metadata": {
            "title": remove_extra_parentheses(video["title"]),
            "artist": [remove_extra_parentheses(artist["name"]) for artist in video["artists"]],
            "album": remove_extra_parentheses(album["name"]) if (album := video.get("album")) else "Unknown Album",
            "lyrics": get_lyrics if not use_yt else None,
            "comment": video['videoId']
        }
    }

    if not use_yt:
        metadata["metadata"]["album_art"] = lambda: retry_on_fail(
            lambda: requests.get(
                video["thumbnails"][0]["url"].replace("=w60-h60", "=w640-h640")
            ).content
        )

    return metadata


def search_query(query, auto=False, use_yt=False, delta=10, use_spotify_album=False):
    if (track := choose_from_spotify(query, auto=auto)) is None:
        return

    metadata = track["metadata"]

    if (video := choose_from_youtube_music(
        query=f"{concat_comma(metadata['artist'])} - {metadata['title']}",
        duration=track["duration"],
        delta=delta,
        auto=auto,
        use_yt=use_yt
    )) is None:
        return

    # it is not recommended
    del video["metadata"]["title"]
    del video["metadata"]["artist"]

    if use_spotify_album:
        if "album" in video["metadata"]:
            del video["metadata"]["album"]

        if "album_art" in video["metadata"]:
            del video["metadata"]["album_art"]

    # update comments to include spotify id
    video["metadata"]["comment"] = f"{track['id']};{video['metadata']['comment']}"

    metadata.update(video["metadata"])

    return track["id"], video["id"], metadata
