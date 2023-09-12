import setuptools

setuptools.setup(
    name='SpotLoad',
    version='1.0',
    packages=["spotload", "ytm"],
    entry_points={
        'console_scripts': [
            'spotload = spotload.__main__:run',
        ]
    },
    requires=[
        "requests==2.28.2",
        "spotipy==2.22.0",
        "mutagen==1.46.0",
        "pathvalidate==2.5.2"
    ],
)
