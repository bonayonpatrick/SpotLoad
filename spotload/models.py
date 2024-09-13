from dataclasses import dataclass, replace
from typing import Optional

import requests

from . import spotify, ytm, utils


@dataclass
class SpotifyTrack:
    id: str
    duration: int
    popularity: int

    album: str
    title: str
    artists: list[str]
    track_number: int
    disc_number: int

    album_art_url: str
    artist_url: str

    year: Optional[int]

    @property
    def name(self):
        return f"{utils.concat_comma(self.artists)} - {self.title}"

    @property
    def url(self):
        return f"https://open.spotify.com/track/{self.id}"

    @property
    def album_art(self):
        if self.album_art_url:
            print("Downloading Album Cover...")
            return utils.retry_on_fail(lambda: requests.get(self.album_art_url).content)

    @property
    def genre(self):
        print("Downloading Genre Metadata...")
        return spotify.artist(self.artist_url)['genres']

    @classmethod
    def from_track(cls, track):
        return cls(
            id=track['id'],
            duration=track['duration_ms'] // 1000,
            popularity=track.get('popularity'),

            album=utils.remove_extra_parentheses(track['album']['name']),
            title=utils.remove_extra_parentheses(track['name']),
            artists=[utils.remove_extra_parentheses(artist['name']) for artist in track['artists']],
            track_number=track['track_number'],
            disc_number=track['disc_number'],
            year=int(dates[0]) if len(dates := track['album']['release_date'].split('-')) == 3 else None,

            album_art_url=track['album']['images'][0]['url'],
            artist_url=track['artists'][0]['external_urls']['spotify']
        )

    @classmethod
    def from_album_track(cls, track, album):
        return cls(
            id=track['id'],
            duration=track['duration_ms'] // 1000,
            popularity=track.get('popularity'),

            album=utils.remove_extra_parentheses(album['name']),
            title=utils.remove_extra_parentheses(track['name']),
            artists=[utils.remove_extra_parentheses(artist['name']) for artist in track['artists']],
            track_number=track['track_number'],
            disc_number=track['disc_number'],
            year=int(dates[0]) if len(dates := album['release_date'].split('-')) == 3 else None,

            album_art_url=album['images'][0]['url'],
            artist_url=track['artists'][0]['external_urls']['spotify']
        )


@dataclass
class YoutubeTrack:
    id: str
    duration: int

    album: str
    title: str
    artists: list[str]
    comment: str

    album_art_url: Optional[str]

    @property
    def lyrics(self):
        print("Downloading Lyrics Metadata.", end='')
        watch_playlist = ytm.get_watch_playlist(self.id)
        if lyrics_id := watch_playlist.get('lyrics'):
            print("..")
            return ytm.get_lyrics(lyrics_id)['lyrics']
        print()

    @property
    def url(self):
        return f"https://youtu.be/{self.id}"

    @property
    def name(self):
        return f"{utils.concat_comma(self.artists)} - {self.title}"

    @property
    def album_art(self):
        if self.album_art_url:
            print("Downloading Album Cover...")
            high_res = self.album_art_url.replace("=w60-h60", "=w640-h640")
            return utils.retry_on_fail(lambda: requests.get(high_res).content)

    @classmethod
    def from_video(cls, video: dict):
        return cls(
            id=video['videoId'],
            duration=video['duration_seconds'],

            title=utils.remove_extra_parentheses(video['title']),
            artists=[utils.remove_extra_parentheses(artist['name']) for artist in video['artists']],
            album=utils.remove_extra_parentheses(album['name']) if (album := video.get('album')) else "Unknown Album",
            comment=video['videoId'],

            album_art_url=video['thumbnails'][0]['url']
            # FIXME: fix thumbnails for youtube videos
        )

    @classmethod
    def from_song(cls, song_data):
        video_details = song_data["videoDetails"]

        return cls(
            id=video_details["videoId"],
            duration=video_details["lengthSeconds"],

            title=utils.remove_extra_parentheses(video_details["title"]),
            artists=[utils.remove_extra_parentheses(video_details["author"])],
            album="Unknown Album",
            comment=video_details["videoId"],

            album_art_url=video_details["thumbnail"]["thumbnails"][0]["url"]
        )


@dataclass
class TrackMetadata:
    spotify: Optional[SpotifyTrack]
    youtube: YoutubeTrack

    title: str
    album: Optional[str]
    album_art: Optional[str]

    artists: list[str]
    genre: Optional[str]
    year: Optional[int]

    track_number: Optional[int]
    disc_number: Optional[int]

    comment: str
    lyrics: str

    @property
    def name(self):
        return f"{utils.concat_comma(self.artists)} - {self.title}"

    @classmethod
    def create(
        cls,
        video: YoutubeTrack,
        track: SpotifyTrack = None,
        use_ytm_album=False,
        use_ytm_title=False
    ):
        if track:
            track = replace(track)

            if use_ytm_album:
                track.album = video.album
                track.album_art_url = video.album_art_url
                album_art = video.album_art
            else:
                album_art = track.album_art

            return cls(
                spotify=track,
                youtube=video,

                album=track.album,
                title=video.title if use_ytm_title else track.title,
                artists=track.artists,
                track_number=track.track_number,
                disc_number=track.disc_number,
                album_art=album_art,
                genre=track.genre,
                year=track.year,
                comment=f"{track.id}:{video.comment}",
                lyrics=video.lyrics
            )
        else:
            return cls(
                spotify=None,
                youtube=video,

                album=video.album,
                title=video.title,
                artists=video.artists,
                track_number=None,
                disc_number=None,
                album_art=video.album_art,
                genre=None,
                year=None,
                comment=f"{video.id}:{video.comment}",
                lyrics=video.lyrics
            )

    def tags(self):
        return utils.remove_empty_fields({
            'title': self.title,
            'album': self.album,
            'album_art': self.album_art,
            'artist': self.artists,
            'genre': self.genre,
            'year': str(self.year),
            'track_number': str(self.track_number),
            'disc_number': str(self.disc_number),
            'comment': self.comment,
            'lyrics': self.lyrics
        })
