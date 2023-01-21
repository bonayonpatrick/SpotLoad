import base64
import os
import shutil
from datetime import datetime

import mutagen
import requests
import ytm
from pathvalidate import sanitize_filename
from spotipy import Spotify, SpotifyClientCredentials

from .chooser import Chooser
from .utils import retry_on_fail, smart_join, reformat_opus


class Spotload:
    def __init__(self, directory):
        self.directory = directory

        self.tag_presets = {
            "album_art": {
                "id3": "APIC:*",
                "opus": "metadata_block_picture"
            },
            "title": {
                "id3": "TIT2",
                "opus": "title"
            },
            "artist": {
                "id3": "TPE1",
                "opus": "artist"
            },
            "track_number": {
                "id3": "TRCK",
                "opus": "tracknumber"
            },
            "disc_number": {
                "id3": "TPOS",
                "opus": "discnumber"
            },
            "album": {
                "id3": "TALB",
                "opus": "album"
            },
            "original_date": {
                "id3": "TDRC",
                "opus": "originaldate"
            },
            "date": {
                "id3": "TDRC",
                "opus": "date"
            },
            "year": {
                "id3": "TDOR",
                "opus": "year"
            },
            "genre": {
                "id3": "TCON",
                "opus": "genre"
            },
            "album_artist": {
                "id3": "TPE2",
                "opus": "albumartist"
            },
            "lyrics": {
                "id3": "USLT:*",
                "opus": "lyrics"
            },
            "comment": {
                "id3": "COMM:*",
                "opus": "comment"
            }
        }

        self.ytm = ytm.YouTubeMusic()

        # using spotdl token
        self.spotify = Spotify(auth_manager=SpotifyClientCredentials(
            client_id="5f573c9620494bae87890c0f08a60293",
            client_secret="212476d9b0f3472eaa762d90b19b0ba8"
        ))

    def choose(self, query, auto=True):
        results = self.spotify.search(q=query)
        tracks = results["tracks"]

        spotify_chooser = Chooser(f"[{tracks['limit']}/{tracks['total']}] Choose Music from Spotify", auto=auto)

        for item in tracks["items"]:
            if item['type'] == "track":
                song_name = item["name"]
                artist = smart_join([artist["name"] for artist in item["artists"]])

                spotify_chooser.add_item(f"{artist} - {song_name}", item)

        if (track := spotify_chooser.choose()) is None:
            return

        artists = [artist["name"] for artist in track["artists"]]

        api = ytm.YouTubeMusic()
        results = api.search_songs(f"{smart_join(artists)} - {track['name']}")

        ytm_chooser = Chooser(f"\n[{len(results['items'])}] Choose Audio from YouTube", auto=auto)
        for result in results["items"]:
            artist = smart_join([artist['name'] for artist in result['artists']])

            # calculate delta to match the closest result
            if abs(result['duration'] - (track["duration_ms"] // 1000)) < 3:
                ytm_chooser.add_item(f"{artist} - {result['name']}", result)

        if (video := ytm_chooser.choose()) is None:
            return

        album = track["album"]
        release_date = album["release_date"]
        ytm_artists = [artist["name"] for artist in video["artists"]]

        metadata = {
            "album_art": retry_on_fail(lambda: requests.get(track["album"]["images"][0]["url"]).content),
            "album": track["album"]["name"],
            "title": video["name"],
            "artist": ytm_artists,
            "track_number": str(track["track_number"]),
            "disc_number": str(track["disc_number"]),
            "genre": self.spotify.artist(track["artists"][0]["external_urls"]["spotify"])["genres"]
        }

        if len(dates := release_date.split("-")) == 3:
            metadata["year"] = dates[0]
        else:
            metadata["original_date"] = release_date
            metadata["date"] = release_date

        return track["id"], video["id"], metadata

    def download(self, video_id, metadata, audio_type="opus"):
        tmp_dir = f"{self.directory}/tmp_{int(datetime.now().timestamp())}"
        os.system(f'yt-dlp -N 8 -f "bestaudio[ext=webm]" -o "{tmp_dir}/%(title)s.opus" "https://youtu.be/{video_id}"')
        filename = os.listdir(tmp_dir)[0]
        audio_path_tmp, audio_path = f"{tmp_dir}/{filename}", f"{self.directory}/{filename}"

        if audio_type == "mp3":
            name, ext = os.path.splitext(filename)
            music_mp3_dir = f"{self.directory}/{name}.mp3"
            print(f"converting {music_mp3_dir}...")
            os.system(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path_tmp}" '
                      f'-acodec libmp3lame -q:a 0 "{music_mp3_dir}"')
            os.remove(f"{audio_path_tmp}")
            self.bind_mp3(music_mp3_dir, metadata)
        elif audio_type == "opus":
            shutil.move(audio_path_tmp, audio_path)
            self.bind_opus(audio_path, metadata)

        os.rmdir(tmp_dir)

    def bind_mp3(self, file_path, tags):
        from mutagen import easyid3
        from mutagen import id3

        audio_file = easyid3.ID3(file_path)
        audio_file.clear()

        id3_tags = {key: val["id3"] for key, val in self.tag_presets.items()}

        for key, val in tags.items():
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
        new_name = f"{smart_join(tags['artist'])} - {tags['title']}.mp3"
        print(f"renaming to {new_name}")
        shutil.move(file_path, f"{os.path.dirname(file_path)}/{sanitize_filename(new_name)}")

    def bind_opus(self, file_path, tags):
        from mutagen.oggopus import OggOpus
        from mutagen import flac

        try:
            audio = OggOpus(file_path)
        except mutagen.oggopus.OggOpusHeaderError:
            reformat_opus(file_path)
            audio = OggOpus(file_path)

        audio.clear()
        opus_tags = {key: val["opus"] for key, val in self.tag_presets.items()}

        for key, val in tags.items():
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
        new_name = f"{smart_join(tags['artist'])} - {tags['title']}.opus"
        print(f"renaming to {new_name}")
        shutil.move(file_path, f"{os.path.dirname(file_path)}/{sanitize_filename(new_name)}")
