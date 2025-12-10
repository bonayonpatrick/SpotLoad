from typing import Iterator

from . import spotify, ytm, utils
from .models import SpotifyTrack, YoutubeTrack, TrackMetadata
from .utils import extract_video_id


def spotify_search(query: str) -> SpotifyTrack:
    track_id = utils.extract_track_id(query)

    tracks = []

    if track_id:
        result = spotify.track(track_id)
        tracks.append(SpotifyTrack.from_track(result))
    else:
        result = spotify.search(q=query)
        for track in result['tracks']['items']:
            if track['type'] == 'track':
                tracks.append(SpotifyTrack.from_track(track))

    track = utils.choose_items(
        title=f"Choose Metadata from Spotify:",
        items=[(track.name, track) for track in tracks]
    )

    if track is None:
        print("no results")
        exit()

    return track


def youtube_search(query: str, duration=0, use_ytm=False, delta=5, auto=False) -> YoutubeTrack:
    video_id = extract_video_id(query)
    result = ytm.search(video_id or query)
    # https://music.youtube.com/watch?v=oUNOZoucEZg&si=ydB8zK0VZBLsVUlm
    tracks = []
    for result in result:
        if result['resultType'] == ('song' if use_ytm else 'video'):
            track = YoutubeTrack.from_video(result)
            print(result)

            if video_id and video_id != result["videoId"]:
                continue
            if result["videoType"] == "MUSIC_VIDEO_TYPE_OMV" and result["duration"] is None:
                tracks.append(track)
            elif result.get("duration_seconds"):  # FIXME: just ignore the empty duration videos for now
                if not use_ytm:  # remove album art when using yt
                    track.album_art_url = None
                if len(track.artists) == 0:
                    continue
                if duration == 0 or (abs(result['duration_seconds'] - duration) < delta):
                    tracks.append(track)

    video = utils.choose_items(
        title=f"Choose Audio from YouTube Music:",
        items=[(f"{track.name} [{track.duration}]", track) for track in tracks],
        match=query,
        auto=auto
    )

    if video is None and video_id is not None:
        video = YoutubeTrack.from_song(ytm.get_song(video_id))

        if not use_ytm:
            video.album_art_url = None

    if video is None:
        print("no results")
        exit()

    return video


def search_query(
    query: str,
    yt_arg: str = None,
    yt_auto=False,
    delta=10,
    use_ytm=True,
    use_ytm_album=False,
    use_ytm_title=False
) -> TrackMetadata:
    track = spotify_search(query=query)

    video = youtube_search(
        query=yt_arg or track.name,
        duration=track.duration,
        delta=delta,
        use_ytm=use_ytm,
        auto=yt_auto
    )

    return TrackMetadata.create(
        video=video,
        track=track,
        use_ytm_album=use_ytm_album if use_ytm else False,
        use_ytm_title=use_ytm_title
    )


def spotify_album(album_url: str) -> Iterator[TrackMetadata]:
    if album_id := utils.extract_album_id(album_url):
        result = spotify.album(album_id)

        for track in result["tracks"]["items"]:
            track = SpotifyTrack.from_album_track(track=track, album=result)
            print(track.name)

            video = youtube_search(
                query=track.name,
                duration=track.duration,
                delta=5,
                use_ytm=True,
                auto=True
            )

            yield TrackMetadata.create(video=video, track=track)
