import argparse
import sys

from spotload import DEFAULT_DIR_PATH, Spotload
from spotload.providers import choose_from_youtube_music, search_query
from spotload.utils import valid_directory, set_default_directory


def run():
    parser = argparse.ArgumentParser(prog='spotload')
    parser.add_argument('--mode', choices=['spot-ytm', 'spot-yt', 'ytm', 'yt'], default='spot-ytm')
    parser.add_argument('--format', choices=['mp3', 'opus'], default='opus')
    parser.add_argument('--default-dir', type=set_default_directory)
    parser.add_argument('--directory', type=valid_directory, default=DEFAULT_DIR_PATH)
    parser.add_argument("--auto", action="store_true")
    parser.add_argument('queries', nargs="*")
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    spotload = Spotload(args.directory or args.default_dir)

    for query in filter(lambda x: bool(x.strip()), args.queries):
        if args.mode in ['ytm', 'yt']:
            metadata = choose_from_youtube_music(query, use_yt=args.mode == 'yt')
            spotload.download_video(spotload.directory, f'https://youtu.be/{metadata["id"]}')
        else:
            result = search_query(query, use_yt=args.mode == 'spot-yt')
            track_id, video_id, metadata = result
            spotload.download(video_id=video_id, metadata=metadata, audio_type=args.format)


if __name__ == '__main__':
    run()
