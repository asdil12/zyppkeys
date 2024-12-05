#!/usr/bin/python3

from setuptools import setup
import os

# Load __version__ from zyppkeys/version.py
exec(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "zyppkeys/version.py")).read())

setup(
    name='zyppkeys',
    version=__version__,
    description='Manage RPM keys',
    author='Dominik Heidler',
    author_email='dheidler@suse.de',
    install_requires=['requests', 'pytz'],
    packages=['zyppkeys'],
    scripts=['bin/zyppkeys'],
)
