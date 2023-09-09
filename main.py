import argparse
import os
import sys

from spotload import Spotload


def valid_directory(pathname):
    if not os.path.exists(pathname):
        os.makedirs(pathname)

    if not os.access(pathname, os.R_OK):
        raise argparse.ArgumentTypeError(f"{pathname} is not accessible.")

    if not os.path.isdir(pathname):
        raise argparse.ArgumentTypeError(f"{pathname} is not a valid directory.")

    return pathname

# TODO: debug prefixes
# TODO: clean up verbose
# TODO: remove some external libraries such as yt-dlp and spotdl


def main():
    parser = argparse.ArgumentParser(prog="spotload")
    parser.add_argument("--format", choices=["mp3", "opus"], default="opus")
    parser.add_argument("--type", choices=["search", "track"], default="search")
    parser.add_argument("--use-yt", action="store_true", default=False)
    parser.add_argument("--bare-yt", action="store_true", default=False)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument("--dir", type=valid_directory, metavar="directory", default=os.getcwd())
    parser.add_argument("queries", nargs="*")

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    args = parser.parse_args()

    if len(args.queries) == 0:
        print("Error: At least one query is required.")
        exit()

    if not args.auto and len(args.queries) > 1:
        print("Error: Only one argument is allowed when --auto is not set.")
        exit()

    spotload = Spotload(args.dir)

    for query in args.queries:
        result = spotload.choose(query, auto=args.auto, use_ytm=not args.use_yt)
        if result is None:
            exit()
        track_id, video_id, metadata = result
        spotload.download(video_id, metadata=metadata, audio_type=args.format)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
