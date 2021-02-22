#!/usr/bin/env python3
# pylint: skip-file

"""Setup for turnovertools package."""

import setuptools

# pylint: disable=invalid-name
# naming conventions per Python packaging guide

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="turnovertools-morgan",
    version="0.0.6",
    author="Morgan Wajda-Levie",
    author_email="morgan.wajdalevie@gmail.com",
    description="Tools for processing Avid Media Composer turnovers.",
    long_description=long_description,
    long_desription_content_type="text/markdown",
    url="https://github.com/morganwl/turnovertools/",
    scripts=['scripts/ryglist.py', 'scripts/edl2csv.py',
             'scripts/vfxpull.py', 'scripts/vfxreference.py',
             'scripts/ale2csv.py', 'scripts/insert_umid.py',
             'scripts/dbplay.py', 'scripts/watermark.py',
             'scripts/vfxreference2.py', 'scripts/csv2markers.py',
             'scripts/csv2ale.py'],
    package_data={'turnovertools': ['adapters/translation_tables/*.csv']},
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS X",
    ],
    python_requires='>=3.7',
)
