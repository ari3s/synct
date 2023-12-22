""" RPM build setup """

import pathlib

from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.md").read_text()
REQUIREMENTS = (HERE / "requirements.txt").read_text().splitlines()
VERSION = (HERE / "VERSION").read_text()

setup(
    name = 'synct',
    version = VERSION,
    description = 'Transform data from source to Google or Excel spreadsheet',
    long_description = README,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/ari3s/synct',
    author = 'Jan Beran',
    author_email = 'ari3s.git@gmail.com',
    license = 'GPL-3.0-or-later',
    zip_safe = False,
    entry_points={
        'console_scripts': ['synct = synct.synct:main']
    },
    packages = find_packages(),
    install_requires = REQUIREMENTS
    )
