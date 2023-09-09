import os
import shutil

import ffmpeg
import requests


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


def choose_index(title, items):
    for item in items:
        print()
    while True:
        try:
            if (index := input("please select an index: ")) == 0:
                return

            return items[index]
        except (ValueError, IndexError):
            print("invalid index")


def smart_join(items):
    if not items:
        return

    last = items.pop() if len(items) > 1 else None
    return " and ".join([", ".join(items)] + ([last] if last else []))


def reformat_opus(file_path):
    print(f"optimizing opus metadata...")

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


def load_album_art(filepath):
    """Making temporary folder for to load ffmpeg output"""

    if not os.path.exists(tmp_folder := f"{os.path.dirname(__file__)}/tmp"):
        os.makedirs(tmp_folder)

    temp = f"{tmp_folder}/album_art.jpg"
    os.system(f'ffmpeg -y -i "{filepath}" -an -vcodec copy "{temp}"')

    with open(temp, "rb") as f1:
        image_bytes = f1.read()

    os.remove(temp)

    return image_bytes


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
            if auto_select:
                print("1")
                return None, 0
            _index = input()
            if prefix and _index.startswith(prefix):
                if value := _index.removeprefix(prefix):
                    if ret_value := callback(value):
                        return ret_value, None
            if 0 < (index := int(_index)) <= len(items):
                return None, index-1
            continue
        except ValueError:
            pass
