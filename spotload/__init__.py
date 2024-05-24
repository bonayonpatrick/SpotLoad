import os.path
import tempfile

from spotipy import Spotify, SpotifyClientCredentials, CacheFileHandler

# using spotdl token
spotify = Spotify(auth_manager=SpotifyClientCredentials(
    cache_handler=CacheFileHandler(cache_path=os.path.join(tempfile.gettempdir(), "spotload.cache")),
    client_id="5f573c9620494bae87890c0f08a60293",
    client_secret="212476d9b0f3472eaa762d90b19b0ba8"
))

from .spotload import Spotload
from pathlib import Path

DEFAULT_DIR_FILEPATH = f"{Path.home()}/spotload_dir"
DEFAULT_DIR_PATH = None

if os.path.exists(DEFAULT_DIR_FILEPATH):
    with open(DEFAULT_DIR_FILEPATH) as f:
        DEFAULT_DIR_PATH = f.read()