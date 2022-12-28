import os
import shutil

import ffmpeg


def choose_index(items):
    while True:
        try:
            return items[int(input("please select an index: "))]
        except (ValueError, IndexError):
            print("invalid index")


def smart_join(items):
    if not items:
        return

    last = items.pop() if len(items) > 1 else None
    return " and ".join([", ".join(items)] + ([last] if last else []))


def reformat_opus(file_path):
    print(f"loading {file_path}")

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

    print("encoding...")
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
