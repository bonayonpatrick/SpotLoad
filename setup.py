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
        "requests",
        "ffmpeg-python==0.2.0",
        "spotipy==2.22.0",
        "mutagen==1.46.0",
        "pathvalidate==2.5.2",
        "youtube-search-python==1.6.6"
    ],
)
