import base64
import json
import os
import platform
import shutil
import sys
from datetime import datetime
from urllib.parse import urlparse

import httpx
import mutagen
import requests
from pathvalidate import sanitize_filename
from spotipy import Spotify, SpotifyClientCredentials
from youtubesearchpython import VideosSearch

from utils import smart_join, reformat_opus, choose_index

os.environ["SPOTIPY_CLIENT_ID"] = "5f573c9620494bae87890c0f08a60293"
os.environ["SPOTIPY_CLIENT_SECRET"] = "212476d9b0f3472eaa762d90b19b0ba8"


class MusicObject:
    def __init__(self, music_dir):
        with open("tag_presets.json") as f:
            self.tag_presets = json.load(f)

        self.spotify = Spotify(auth_manager=SpotifyClientCredentials())
        self.tags = {}

        self.music_dir = music_dir

    def download(self, query, audio_type="opus"):
        results = self.spotify.search(q=query)
        tracks = results["tracks"]

        search_results = []
        count = 0

        print(f"[{tracks['limit']}/{tracks['total']}] Choose Music from Spotify:")
        for item in tracks["items"]:
            if item['type'] == "track":
                song_name = item["name"]
                artist = smart_join([artist["name"] for artist in item["artists"]])
                print(f"  [{count}] {artist} - {song_name}")

                count += 1
                search_results.append(item)

        return self.download_spotify_track(choose_index(search_results), audio_type)

    def download_spotify_track(self, track, audio_type="opus"):
        if isinstance(track, str):
            if track.startswith("https://"):
                spt = urlparse(track).path.split("/")

                if spt[1] != "track":
                    return f"invalid url: {track}"

                track = spt[2]

            track = self.spotify.track(track)

        if track['type'] != "track":
            return

        album = track["album"]
        song_name = track["name"]

        artist = smart_join([artist["name"] for artist in track["artists"]])

        track_data = {
            "url": track["external_urls"]["spotify"],
            "disc": track["disc_number"],
            "track": track["track_number"],
            "release_date": album["release_date"],
            "name": song_name,
            "artist": artist,
            "album": album["name"],
            "duration": (track["duration_ms"] // 1000)
        }

        search_query = f"\"{track_data['artist']} - {track_data['name']}\" audio"

        while True:
            try:
                videos = VideosSearch(search_query, limit=50)
                break
            except httpx.ConnectError:
                print("connection error")

        results = videos.result().get("result")

        yt_urls = []
        count = 0

        print("\nChoose Audio from YouTube:")
        for result in results:
            title = result.get("title")
            video_id = result.get("id")
            url = f"https://youtu.be/{video_id}"
            # views = result.get("viewCount").get("text")
            channel_name = result.get("channel").get("name")
            duration = result.get("duration")
            duration_spl = duration.split(":")
            minutes, seconds = int(duration_spl[0]), int(duration_spl[1])
            total_sec = (minutes * 60) + seconds
            delta = abs(total_sec - track_data["duration"])

            if delta < 2:
                print(f"  [{count}] [{channel_name}] {title}")
                yt_urls.append(url)
                count += 1

        return track["id"], self.youtube_music(choose_index(yt_urls), audio_type)

    def youtube_music(self, url, audio_type="opus"):
        tmp_dir = f"{self.music_dir}/tmp_{int(datetime.now().timestamp())}"
        os.system(f'yt-dlp -N 8 -f "bestaudio[ext=webm]" -o "{tmp_dir}/%(title)s.opus" "{url}"')
        filename = os.listdir(tmp_dir)[0]
        audio_path_tmp, audio_path = f"{tmp_dir}/{filename}", f"{self.music_dir}/{filename}"

        if audio_type == "mp3":
            name, ext = os.path.splitext(filename)
            music_mp3_dir = f"{self.music_dir}/{name}.mp3"
            print(f"converting {music_mp3_dir}...")
            os.system(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path_tmp}" '
                      f'-acodec libmp3lame -q:a 0 "{music_mp3_dir}"')
            os.remove(f"{audio_path_tmp}")
            audio_path = music_mp3_dir
        elif audio_type == "opus":
            shutil.move(audio_path_tmp, audio_path)

        os.rmdir(tmp_dir)
        return audio_path

    def load_spotify_track(self, track_id):
        result = self.spotify.track(track_id)

        album = result["album"]
        artists = smart_join([artist["name"] for artist in result["artists"]])
        album_artists = smart_join([artist["name"] for artist in album["artists"]])
        release_date = album["release_date"]

        self.tags = {
            "album_art": requests.get(album["images"][0]["url"]).content,
            "album": album["name"],
            "title": result["name"],
            "artist": artists,
            "track_number": str(result["track_number"]),
            "disc_number": str(result["disc_number"]),
            "genre": "unknown",
            "album_artist": album_artists
        }

        if len(dates := release_date.split("-")) == 3:
            self.tags["year"] = dates[0]
        else:
            self.tags["original_date"] = release_date
            self.tags["date"] = release_date

    def bind_mp3(self, file_path):
        from mutagen import easyid3
        from mutagen import id3

        audio_file = easyid3.ID3(file_path)
        audio_file.clear()

        id3_tags = {key: val["id3"] for key, val in self.tag_presets.items()}

        for key, val in self.tags.items():
            print(f"Binding {key} with value: {val[:20]}")

            if key == "album_art":
                print("Binding APIC Cover")
                audio_file["APIC"] = id3.APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=val)
            elif key == "lyrics":
                audio_file.add(id3.COMM(encoding=3, text=val))
            elif key == "comment":
                audio_file["USLT::'eng'"] = id3.USLT(encoding=3, lang=u"eng", desc=u"desc", text=val)
            else:
                print(f"Converting {key} to {id3_tags[key]}")
                audio_file[id3_tags[key]] = getattr(id3, id3_tags[key])(encoding=3, text=val)

        audio_file.save(v2_version=3)

    def bind_opus(self, file_path):
        from mutagen.oggopus import OggOpus
        from mutagen import flac

        try:
            audio = OggOpus(file_path)
        except mutagen.oggopus.OggOpusHeaderError:
            reformat_opus(file_path)
            audio = OggOpus(file_path)

        audio.clear()
        opus_tags = {key: val["opus"] for key, val in self.tag_presets.items()}

        for key, val in self.tags.items():
            if key == "album_art":
                image = flac.Picture()
                image.type = 3
                image.desc = "Cover"
                image.mime = "image/jpeg"
                image.data = val

                audio[opus_tags[key]] = base64.b64encode(image.write()).decode("ascii")
                print(f"binding cover art...")
            else:
                print(f"binding opus tag: {key}")
                audio[opus_tags[key]] = val

        audio.save()
        new_name = f"{self.tags['artist']} - {self.tags['title']}.opus"
        print(f"renaming to {new_name}")
        shutil.move(file_path, f"{os.path.dirname(file_path)}/{sanitize_filename(new_name)}")


def main():
    if len(sys.argv) != 3:
        return

    audio_type = "opus"

    if platform.system() == "Windows":
        obj = MusicObject("D:/PATRICK DRIVE/Music")
    else:
        obj = MusicObject("/storage/emulated/0/Music")

    if sys.argv[1] == "search":
        track_id, local_file = obj.download(sys.argv[2], audio_type)
    elif sys.argv[1] == "track":
        track_id, local_file = obj.download_spotify_track(sys.argv[2], audio_type)
    else:
        print(f"invalid selection {sys.argv[1]}")
        return

    obj.load_spotify_track(track_id)

    if audio_type == "opus":
        obj.bind_opus(local_file)
    elif audio_type == "mp3":
        obj.bind_mp3(local_file)


if __name__ == '__main__':
    main()
