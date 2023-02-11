from youtubesearchpython import VideosSearch

from spotload.chooser import Chooser


def choose_from_youtube(query, duration=0, delta=3, auto=False):
    results = VideosSearch(query, limit=20).result().get("result")

    yt_chooser = Chooser(f"\n[{len(results)}] Choose Audio from YouTube", auto=auto)
    for result in results:
        duration_spl = result.get("duration").split(":")
        minutes, seconds = int(duration_spl[0]), int(duration_spl[1])
        total_sec = (minutes * 60) + seconds

        # calculate delta to match the closest result
        if (abs(total_sec - duration) < delta) or duration == 0 and result["type"] == "video":
            result["duration"] = total_sec
            yt_chooser.add_item(f"{result.get('channel').get('name')} - {result['title']}", result)

    if (video := yt_chooser.choose()) is None:
        return

    return {
        "id": video["id"],
        "title": video["title"],
        "duration": video["duration"],
        "channel_name": video["channel"]["name"]
    }
