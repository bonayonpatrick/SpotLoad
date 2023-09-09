from spotipy import Spotify, SpotifyClientCredentials

# using spotdl token
spotify = Spotify(auth_manager=SpotifyClientCredentials(
    client_id="5f573c9620494bae87890c0f08a60293",
    client_secret="212476d9b0f3472eaa762d90b19b0ba8"
))

from .spotload import Spotload
