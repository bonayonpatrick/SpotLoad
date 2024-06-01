import setuptools

setuptools.setup(
    name='SpotLoad',
    version='1.0',
    packages=["spotload"],
    entry_points={
        'console_scripts': [
            'spotload = spotload.__main__:run',
        ]
    },
    python_requires=">=3.8",
    install_requires=[
        'yt-dlp',
        'setuptools',
        'requests',
        'ffmpeg-python==0.2.0',
        'spotipy==2.22.1',
        'mutagen==1.46.0',
        'pathvalidate==2.5.2',
        'pathlib==1.0.1',
        'ytmusicapi==1.7.2'
    ],
)
