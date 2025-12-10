import base64
import os
import shutil
from datetime import datetime

import ffmpeg
import mutagen
from pathvalidate import sanitize_filename

from . import create_temp
from .models import TrackMetadata

tag_presets = {
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


def reformat_opus(file_path: str):
    print(f"Re-encoding OPUS File...")

    dirpath, filename = os.path.dirname(file_path), os.path.basename(file_path)

    tmp_dir = f"{dirpath}/tmp"
    tmp_file = os.path.join(tmp_dir, filename)

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    probe = ffmpeg.probe(file_path)
    format_type = probe["format"]
    streams = probe["streams"]

    if (codec := streams[0]["codec_name"]) != "opus":
        print(f"type {codec} not supported.")
        return

    if not format_type:
        print("invalid format type.")
        return

    if not (tags := format_type.get("tags")):
        tags = streams[0]["tags"]

    if not tags or tags["encoder"] not in ["google/video-file", "google"]:
        print(f"{filename} is already in a good shape: {tags}")
        return

    os.system(f'ffmpeg -hide_banner -loglevel error -y -i "{file_path}" -acodec copy "{tmp_file}"')

    shutil.copyfile(tmp_file, file_path)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def download_video(filepath: str, urls: list[str] | str) -> int:
    if isinstance(urls, str):
        urls = [urls]

    return os.system(" ".join([
        f'yt-dlp',
        f'-f "bestaudio[ext=webm]/bestaudio[ext=m4a]"',
        f'-o "{filepath}"',
        f'--external-downloader aria2c' if shutil.which("aria2c") else "",
        f'--fragment-retries 999',
        f'--abort-on-unavailable-fragment',
        " ".join([f'"{url}"' for url in urls])
    ]))


def download(metadata: TrackMetadata, directory: str, audio_type="opus"):
    filename = sanitize_filename(f"{metadata.name}.{audio_type}")
    filepath = f"{directory}/{filename}"

    if not os.path.exists(filepath):
        download_tmp = create_temp(f"spotload.{int(datetime.now().timestamp())}.webm")
        code = download_video(download_tmp, metadata.youtube.url)

        if code != 0:
            print(f"[{code}] Unknown error from yt-dlp")
            exit(code)

        if audio_type == "mp3":
            print(f"Converting file to MP3...")
            os.system(f'ffmpeg -hide_banner -loglevel error -y -i "{download_tmp}" '
                      f'-acodec libmp3lame -q:a 0 "{filepath}"')
            os.remove(f"{download_tmp}")
        elif audio_type == "opus":
            shutil.move(download_tmp, filepath)
    else:
        print("File already exists.")

    if audio_type == "mp3":
        print(f"Binding Metadata to MP3...")
        bind_mp3(filepath, metadata.tags())
    elif audio_type == "opus":
        print(f"Binding Metadata to OPUS...")
        bind_opus(filepath, metadata.tags())

    print(f"File saved to {filepath}")


def bind_mp3(file_path: str, tags: dict):
    from mutagen import easyid3
    from mutagen import id3

    audio_file = easyid3.ID3(file_path)
    audio_file.clear()

    id3_tags = {key: val["id3"] for key, val in tag_presets.items()}

    for key, val in tags.items():
        if key == "album_art":
            audio_file["APIC"] = id3.APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=val)
        elif key == "lyrics":
            audio_file.add(id3.COMM(encoding=3, text=val))
        elif key == "comment":
            audio_file["USLT::'eng'"] = id3.USLT(encoding=3, lang=u"eng", desc=u"desc", text=val)
        else:
            audio_file[id3_tags[key]] = getattr(id3, id3_tags[key])(encoding=3, text=val)

    audio_file.save(v2_version=3)


def bind_opus(file_path: str, tags: dict):
    from mutagen.oggopus import OggOpus
    from mutagen import flac

    try:
        audio = OggOpus(file_path)
    except mutagen.oggopus.OggOpusHeaderError:
        reformat_opus(file_path)
        audio = OggOpus(file_path)

    audio.clear()
    opus_tags = {key: val["opus"] for key, val in tag_presets.items()}

    for key, val in tags.items():
        if key == "album_art":
            image = flac.Picture()
            image.type = 3
            image.desc = "Cover"
            image.mime = "image/jpeg"
            image.data = val

            audio[opus_tags[key]] = base64.b64encode(image.write()).decode("ascii")
        else:
            audio[opus_tags[key]] = val

    audio.save()
