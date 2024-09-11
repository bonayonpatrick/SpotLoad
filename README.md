# A Simple YouTube Music Downloader with Metadata

## Usage

### Set Default Download Directory

To specify the default download directory, use the following command:

```bash
python main.py --default-dir "/storage/emulated/0/Music"
```

### Available Modes

- **spot-ytm:** Download YouTube music with Spotify metadata.
- **spot-yt:** Download a YouTube video with Spotify metadata.
- **yt:** Download a YouTube video.
- **ytm:** Download YouTube music with YouTube Music metadata.
- **spot-album (experimental):** Download multiple YouTube music tracks with Spotify album metadata.

### Examples

- **Download Music with Spotify Metadata:**

  ```bash
  python main.py --mode spot-ytm "colbreakz 10000"
  ```

- **Download Music with Spotify Metadata from a URL:**

  ```bash
  python main.py --mode spot-ytm "https://open.spotify.com/track/2fWxJpE8vubVqPgpVFP3F8"
  ```

- **Download Music with YouTube Music Metadata from a URL:**

  ```bash
  python main.py --mode ytm "https://youtu.be/ilafD9HQ8GU"
  ```

### Download Format

The default download format is OPUS. To download music in MP3 format, use the following command:

```bash
python main.py --mode spot-ytm --format mp3 "codebreakz 10000"
```
