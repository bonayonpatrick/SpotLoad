import argparse
import sys

import requests.exceptions

from spotload import DEFAULT_DIR_PATH, SpotLoad
from spotload.providers import choose_from_youtube_music, search_query
from spotload.utils import valid_directory, set_default_directory, download_video


def run():
    try:
        main()
    except KeyboardInterrupt:
        pass
    except requests.exceptions.ConnectionError:
        print("Unreachable network.")
    except KeyError as e:
        print(e)

def main():
    parser = argparse.ArgumentParser(prog='spotload')
    parser.add_argument('--mode', choices=['spot-ytm', 'spot-yt', 'ytm', 'yt'], default='spot-ytm')
    parser.add_argument('--format', choices=['mp3', 'opus'], default='opus')
    parser.add_argument('--default-dir', type=set_default_directory)
    parser.add_argument('--directory', type=valid_directory, default=DEFAULT_DIR_PATH)

    parser.add_argument('--delta', type=int, default=10)
    parser.add_argument('--use-spotify-album', action="store_true")
    parser.add_argument("--auto", action="store_true")
    parser.add_argument('queries', nargs="*")

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    spotload = SpotLoad(args.directory or args.default_dir)

    for query in filter(lambda x: bool(x.strip()), args.queries):
        if args.mode in ['ytm', 'yt']:
            video_data = choose_from_youtube_music(query, auto=args.auto, use_yt=args.mode == 'yt')
            video_id, metadata = video_data["id"], video_data["metadata"]
        else:
            result = search_query(
                query=query,
                auto=args.auto,
                use_yt=args.mode == 'spot-yt',
                delta=args.delta,
                use_spotify_album=args.use_spotify_album
            )
            track_id, video_id, metadata = result
        spotload.download(video_id, metadata, args.format)


if __name__ == '__main__':
    run()


# TODO: add prefix input inside of item selection interpretation