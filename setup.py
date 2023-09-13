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
    dependency_links=[
        "ytm @ git+https://github.com/tombulled/python-youtube-music.git#master"
    ],
    install_requires=[
        "requests==2.28.2",
        "urllib3==1.26.13",
        "spotipy==2.22.0",
        "mutagen==1.46.0",
        "pathvalidate==2.5.2"
    ],
)
