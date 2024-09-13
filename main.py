import argparse
import os
import sys

import requests.exceptions
from pathvalidate import sanitize_filename

from spotload import DEFAULT_DIR_PATH
from spotload.core import download
from spotload.models import TrackMetadata
from spotload.spotload import search_query, youtube_search, spotify_album
from spotload.utils import set_default_directory, valid_directory, create_folder


def run():
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except requests.exceptions.ConnectionError:
        print("Unreachable network.")


def main():
    parser = argparse.ArgumentParser(prog='spotload')
    parser.add_argument('--mode', choices=['spot-ytm', 'spot-yt', 'ytm', 'yt', 'spot-album'], default='spot-ytm')
    parser.add_argument('--format', choices=['mp3', 'opus'], default='opus')

    parser.add_argument('--default-dir', type=set_default_directory)
    parser.add_argument('--directory', type=valid_directory, default=DEFAULT_DIR_PATH)

    parser.add_argument('--delta', type=int, default=10)
    parser.add_argument('--use-ytm-album', action="store_true")
    parser.add_argument('--use-ytm-title', action="store_true")

    parser.add_argument('--yt-arg', type=str)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument('arg')

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    directory = args.directory or args.default_dir

    if args.mode in ['spot-album']:
        for metadata in spotify_album(args.arg):
            album_dir = create_folder(os.path.join(directory, sanitize_filename(metadata.album)))
            download(metadata, album_dir, args.format)
        return

    if args.mode in ['ytm', 'yt']:
        video = youtube_search(query=args.arg, use_ytm=args.mode == 'ytm')
        track_metadata = TrackMetadata.create(video)
    else:
        track_metadata = search_query(
            query=args.arg,
            yt_arg=args.yt_arg,
            use_ytm=args.mode == 'spot-ytm',
            delta=args.delta,
            use_ytm_album=args.use_ytm_album,
            use_ytm_title=args.use_ytm_title,
            yt_auto=args.auto
        )

    download(track_metadata, directory, args.format)


if __name__ == '__main__':
    run()
