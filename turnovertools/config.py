"""Global configuration object with defaults."""

import os

class Config(object):
    CLEAN_MEDIA_PATH = '/Volumes/GoogleDrive/My Drive/1015_Project Looking Glass/04_FILMMAKING_WORKING_FILES/TURNOVERS/Reels_Clean SameAsSource'
    DEFAULT_FRAMERATE = '23.976'
    DEFAULT_HANDLES = 8
    FILEMAKER_APPLICATION = 'FileMaker Pro 18 Advanced'
    MXFDB = os.path.join(os.path.expanduser("~"), '.mxfdb.db')
