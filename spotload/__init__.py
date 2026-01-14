import os
from pathlib import Path

from spotipy import Spotify, SpotifyClientCredentials, CacheFileHandler
from ytmusicapi import YTMusic

from .utils import create_temp

DEFAULT_DIR_FILEPATH = f"{Path.home()}/.spotload_dir"
DEFAULT_DIR_PATH = "."

if os.path.exists(DEFAULT_DIR_FILEPATH):
    with open(DEFAULT_DIR_FILEPATH) as f:
        DEFAULT_DIR_PATH = f.read()

# spotify = Spotify(auth_manager=SpotifyClientCredentials(
#     cache_handler=CacheFileHandler(cache_path=create_temp("spotload.cache")),
#     client_id="5f573c9620494bae87890c0f08a60293",
#     client_secret="212476d9b0f3472eaa762d90b19b0ba8"
# ))

spotify = Spotify(auth_manager=SpotifyClientCredentials(
    cache_handler=CacheFileHandler(cache_path=create_temp("spotload.1.cache")),
    client_id="5ac57ff000b14c9c81c25a3c95dc61d1",
    client_secret="a6a26c174f794a898322228665257388"
))

ytm = YTMusic()
