import argparse
import os
import shutil
from urllib.parse import urlparse, parse_qs

import ffmpeg
import requests


def download_video(directory, urls):
    if isinstance(urls, str):
        urls = [urls]

    return os.system(" ".join([
        f'yt-dlp',
        f'-f "bestaudio[ext=webm]"',
        f'-o "{directory}/%(title)s.opus"',
        f'--external-downloader aria2c' if shutil.which("aria2c") else "",
        f'--fragment-retries 999',
        f'--abort-on-unavailable-fragment',
        " ".join([f'"{url}"' for url in urls])
    ]))


def reformat_opus(file_path):
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
        print(f"{filename} is already optimized: {tags}")
        return

    # print("encoding...")
    os.system(f'ffmpeg -hide_banner -loglevel error -y -i "{file_path}" -acodec copy "{tmp_file}"')

    shutil.copyfile(tmp_file, file_path)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def retry_on_fail(call, *args, **kwargs):
    kwargs.setdefault("max_retries", 10)
    max_retries = kwargs.pop("max_retries")

    retries = 0

    while retries < max_retries:
        try:
            return call(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print(f"connection failed: {retries}")
            retries += 1


def concat_comma(items):
    items = items[:]

    if not items:
        return

    last = items.pop() if len(items) > 1 else None
    return " and ".join([", ".join(items)] + ([last] if last else []))


def choose_items(title: str, items: list, prefix: str = None, callback: callable = None, auto_select: bool = False):
    if not items:
        print("no results")
        exit(0)
    print(title)
    for i, item in enumerate(items, 1):
        print(f" {str(i):>2}: {item}")
    while True:
        try:
            print("<<: ", end="")
            if auto_select or len(items) == 1:
                print("1 (auto-select)")
                return None, 0
            _index = input()
            if prefix and _index.startswith(prefix):
                if value := _index.removeprefix(prefix):
                    if ret_value := callback(value):
                        return ret_value, None
            if 0 < (index := int(_index)) <= len(items):
                return None, index - 1
            continue
        except ValueError:
            pass


def valid_directory(pathname: str):
    if not os.path.exists(pathname):
        os.makedirs(pathname)

    if not os.access(pathname, os.R_OK):
        raise argparse.ArgumentTypeError(f"{pathname} is not accessible.")

    if not os.path.isdir(pathname):
        raise argparse.ArgumentTypeError(f"{pathname} is not a valid directory.")

    pathname = pathname.strip()
    return pathname


def set_default_directory(pathname):
    from spotload import DEFAULT_DIR_FILEPATH

    pathname = valid_directory(pathname)

    print(f"default directory changed to {pathname}")
    with open(DEFAULT_DIR_FILEPATH, "w") as f:
        f.write(pathname)

    exit()



def extract_video_id(url):
    parsed_url = urlparse(url)

    video_id = None
    if parsed_url.netloc == "youtu.be":
        video_id = parsed_url.path.replace("/", "")
    elif parsed_url.netloc in ["music.youtube.com", "youtube.com", "m.youtube.com", "www.youtube.com"]:
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]

    return video_id

