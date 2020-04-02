#!/usr/bin/env python3

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="turnovertools-morgan",
    version="0.0.3",
    author="Morgan Wajda-Levie",
    author_email="morgan.wajdalevie@gmail.com",
    description="Tools for processing Avid Media Composer turnovers.",
    long_description=long_description,
    long_desription_content_type="text/markdown",
    url="https://github.com/morganwl/turnovertools/",
    scripts=['scripts/xml2ryg2.py', 'scripts/edl2csv.py'],
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS X",
    ],
    python_requires='>=3.7',
)
