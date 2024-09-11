import argparse
import difflib
import os
import re
import tempfile
from typing import Any
from urllib.parse import urlparse, parse_qs

import requests


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def create_temp(filename):
    return os.path.join(tempfile.gettempdir(), filename)


def remove_empty_fields(data: dict) -> dict:
    return {key: val for key, val in data.items() if val is not None}


def concat_comma(items):
    items = items[:]

    if not items:
        return

    last = items.pop() if len(items) > 1 else None
    return " and ".join([", ".join(items)] + ([last] if last else []))


def remove_extra_parentheses(text):
    pattern = re.compile(r'(.+?)\s\(\1\)')
    return pattern.sub(r'\1', text)


def retry_on_fail(call, *args, **kwargs):
    kwargs.setdefault('max_retries', 10)
    max_retries = kwargs.pop('max_retries')

    retries = 0

    while retries < max_retries:
        try:
            return call(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print(f"Connection failed: {retries}")
            retries += 1


def choose_items(title: str, items: list[tuple[str, Any]], match: str = None, auto=False, match_ratio=90):
    matches = []

    if not items:
        return

    print(title)

    if match:
        items = list(filter(lambda x: difflib.SequenceMatcher(None, match, x[0]).ratio() < match_ratio, items))

    for i, (key, item) in enumerate(items, 1):
        print(f" {str(i):>2}: {key}")
        if key == match:
            matches.append(i - 1)

    while True:
        try:
            print("<<: ", end="")
            if len(matches) == 1:
                print(f"{matches[0] + 1} (auto-select)")
                return items[matches[0]][1]  # select the first matched item
            if auto or len(items) == 1:
                print("1 (auto-select)")
                return items[0][1]  # select the first item
            _index = input()
            if 0 < (index := int(_index)) <= len(items):
                return items[index - 1][1]
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


def extract_track_id(url: str) -> str:
    if match := re.search(r"track/([a-zA-Z0-9]+)", url):
        return match.group(1)


def extract_album_id(url: str) -> str:
    if match := re.search(r"album/([a-zA-Z0-9]+)", url):
        return match.group(1)
