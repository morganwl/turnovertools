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
    version="0.0.7.2",
    author="Morgan Wajda-Levie",
    author_email="morgan.wajdalevie@gmail.com",
    description="Tools for processing Avid Media Composer turnovers.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/morganwl/turnovertools/",
    scripts=['scripts/edl2csv.py',
             'scripts/vfxpull.py',
             'scripts/ale2csv.py', 'scripts/insert_umid.py',
             'scripts/dbplay.py', 'scripts/watermark.py',
             'scripts/vfxreference2.py', 'scripts/csv2markers.py',
             'scripts/csv2ale.py', 'scripts/prepsubmission.py',
             'quick/files2csv.py',
             'quick/simedl.py',
             'quick/email2submission.py',
             'quick/stock2csv.py'],
    package_data={'turnovertools': ['adapters/translation_tables/*.csv']},
    data_files=[('.', ['INSTALL.command'])],
    packages=setuptools.find_packages(),
    install_requires=['timecode',
                      'edl',
                      'ffmpeg-python',
                      'future==0.18.2',
                      'python-dateutil'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS X",
    ],
    python_requires='>=3.7',
)
