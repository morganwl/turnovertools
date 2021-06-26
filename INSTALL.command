#!/bin/bash

cd $(dirname "$BASH_SOURCE")

# If python3 is not on the path, download the MacPython installer and open it
if [ ! -x "$(command -v python3)" ];
then
    echo "Downloading python installer. Rerun this script once python3 is successfully installed."
    curl -L -o python_installer.pkg "https://www.python.org/ftp/python/3.9.5/python-3.9.5-macosx10.9.pkg"
    open python_installer.pkg
    exit 1
fi

if [ ! -f "venv/bin/activate" ];
then
    python3 -m venv venv
    source venv/bin/activate
fi

# If ffmpeg is not on the path, install it into the virtual environment
if [ ! -x "$(command -v ffmpeg)" ];
then
    curl -L -o ffmpeg.zip "https://evermeet.cx/ffmpeg/get/zip"
    unzip ffmpeg.zip
    mv ffmpeg "venv/bin"
    rm ffmpeg.zip
fi

if [ ! -x "$(command -v ffprobe)" ];
then
    curl -L -o ffprobe.zip "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip"
    unzip ffprobe.zip
    mv ffprobe "venv/bin"
    rm ffprobe.zip
fi

pip install timecode
pip install -e .

TTOOLSPATH=$PWD/venv/bin
echo -n ${TTOOLSPATH} | pbcopy
osascript -e "display dialog \"${TTOOLSPATH} has been copied to the clipboard. Paste it into the turnovertools_path field of Advanced->Config in the FileMaker database. You can run this script again at any time to get this value.\""

