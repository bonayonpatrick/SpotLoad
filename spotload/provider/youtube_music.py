import ytm

from spotload.chooser import Chooser
from spotload.utils import smart_join


def choose_from_youtube_music(query, duration=0, delta=3, auto=False):
    api = ytm.YouTubeMusic()
    results = api.search_songs(query)

    ytm_chooser = Chooser(f"\n[{len(results['items'])}] Choose Audio from YouTube Music", auto=auto)
    for result in results["items"]:
        artist = smart_join([artist['name'] for artist in result['artists']])

        # calculate delta to match the closest result
        if (abs(result['duration'] - duration) < delta) or duration == 0:
            ytm_chooser.add_item(f"{artist} - {result['name']}", result)

    if (video := ytm_chooser.choose()) is None:
        return

    return {
        "id": video["id"],
        "duration": video["duration"],
        "metadata": {
            "title": video["name"],
            "artists": [artist["name"] for artist in video["artists"]],
            "album": video["album"]["name"]
        }
    }
