import base64
import os
import shutil
from datetime import datetime

import mutagen
from pathvalidate import sanitize_filename

from .utils import concat_comma, reformat_opus, download_video


class SpotLoad:
    def __init__(self, directory=os.getcwd()):
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

    def download(self, video_id, metadata, audio_type="opus"):
        tmp_dir = f"{self.directory}/tmp_{int(datetime.now().timestamp())}"
        download_video(tmp_dir, f"https://youtu.be/{video_id}")

        if album_art := metadata.get("album_art"):
            print("Downloading Album Cover...")
            metadata["album_art"] = album_art()
        if genre := metadata.get("genre"):
            print("Downloading Genre Metadata...")
            metadata["genre"] = genre()
        if lyrics := metadata.get("lyrics"):
            print("Downloading Lyrics Metadata...")
            metadata["lyrics"] = lyrics()

        filename = os.listdir(tmp_dir)[0]
        audio_path_tmp, audio_path = f"{tmp_dir}/{filename}", f"{self.directory}/{filename}"

        if audio_type == "mp3":
            name, ext = os.path.splitext(filename)
            music_mp3_dir = f"{self.directory}/{name}.mp3"
            print(f"Converting file to MP3...")
            os.system(f'ffmpeg -hide_banner -loglevel error -y -i "{audio_path_tmp}" '
                      f'-acodec libmp3lame -q:a 0 "{music_mp3_dir}"')
            os.remove(f"{audio_path_tmp}")
            print(f"Binding Metadata to MP3...")
            self.bind_mp3(music_mp3_dir, metadata)
        elif audio_type == "opus":
            shutil.move(audio_path_tmp, audio_path)
            print(f"Binding Metadata to OPUS...")
            self.bind_opus(audio_path, metadata)

        os.rmdir(tmp_dir)

    def bind_mp3(self, file_path, tags):
        from mutagen import easyid3
        from mutagen import id3

        audio_file = easyid3.ID3(file_path)
        audio_file.clear()

        id3_tags = {key: val["id3"] for key, val in self.tag_presets.items()}

        for key, val in tags.items():
            # print(f"Binding {key} with value: {val[:20]}")

            if key == "album_art":
                # print("Binding APIC Cover")
                audio_file["APIC"] = id3.APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=val)
            elif key == "lyrics":
                audio_file.add(id3.COMM(encoding=3, text=val))
            elif key == "comment":
                audio_file["USLT::'eng'"] = id3.USLT(encoding=3, lang=u"eng", desc=u"desc", text=val)
            else:
                # print(f"Converting {key} to {id3_tags[key]}")
                if tag := id3_tags.get(key):
                    audio_file[tag] = getattr(id3, id3_tags[key])(encoding=3, text=val)

        audio_file.save(v2_version=3)
        new_name = f"{concat_comma(tags['artist'])} - {tags['title']}.mp3"
        # print(f"renaming to {new_name}")
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
                # print(f"binding cover art...")
            else:
                # print(f"binding opus tag: {key}")
                if tag := opus_tags.get(key):
                    audio[tag] = val

        audio.save()
        new_name = f"{concat_comma(tags['artist'])} - {tags['title']}.opus"
        # print(f"renaming to {new_name}")
        shutil.move(file_path, f"{os.path.dirname(file_path)}/{sanitize_filename(new_name)}")
