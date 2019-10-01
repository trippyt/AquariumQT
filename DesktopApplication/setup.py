from setuptools import setup

setup(
    name='aquariumqt',
    version='0.0.0',
    author='TrippyT',
    author_email='user@example.com',
    #url='',
    packages=['aquariumqt'],
    entry_points={
        'console_scripts': [
            'aquariumqt = aquariumqt.app:main',
        ]
    },
    install_requires=['PyQt5'],
)
