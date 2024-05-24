import argparse
import os
import re

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


def concat_comma(items):
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


def extract_video_id(youtube_url):
    # Regular expression to match YouTube video ID
    pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.match(pattern, youtube_url)
    if match:
        return match.group(1)
    else:
        return None