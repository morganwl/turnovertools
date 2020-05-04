import turnovertools.mediaobjects as mobs

class FromFileMaker:
    """Accepts a row from a FileMaker table and converts it to a mobs
    object."""
    translation_table = {}

    @classmethod
    def to_clip(cls, record):
        """Accepts a dictionary and converts it to a clip object."""
