import setuptools

setuptools.setup(
    name='SpotLoad',
    version='1.0',
    entry_points={
    'console_scripts': [
        'spotload = spotload.__main__:run',
    ],
})
