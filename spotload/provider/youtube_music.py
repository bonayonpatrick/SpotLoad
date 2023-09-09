import ytm

from ..utils import smart_join, choose_items


def choose_from_youtube_music(query, duration=0, delta=3, auto=False):
    api = ytm.YouTubeMusic()
    items = api.search_songs(query)["items"]

    _items = {}
    for item in items:
        artist = smart_join([artist['name'] for artist in item['artists']])
        # calculate delta to match the closest result
        if (abs(item['duration'] - duration) < delta) or duration == 0:
            _items[f"{artist} - {item['name']}"] = item

    def _prefix_action(video_id):
        if result := api.song(video_id):
            return result
        print("invalid video id")

    video, index = choose_items(
        title=f"Choose Audio from YouTube Music",
        items=_items.keys(),
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
