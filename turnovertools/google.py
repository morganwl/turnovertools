"""Mixin classes for Google Creative Lab workflows."""

from turnovertools import mediaobjects as mobs

# pylint: disable=too-few-public-methods
# this is a mixin class meant for its attributes
class Google:
    """Mixin class to provide expected behavior for attributes used in
    Google Creative Lab workflows to mobs objects."""

    _provides_attrs = ['link', 'source_type', 'source_from', 'pulled_by',
                       'source_status', 'ryg']

    def __init__(self, *args, link=None, source_type=None, source_from=None,
                 pulled_by=None, source_status=None, ryg=None,
                 **kwargs):
        self.link = link
        self.source_type = source_type
        self.source_from = source_from
        self.pulled_by = pulled_by
        self.source_status = source_status
        self.ryg = ryg
        super().__init__(*args, **kwargs)

    @classmethod
    def dummy(cls, **kwargs):
        """Creates a dummy object with generic, properly formed values."""
        defaults = dict(link='https://www.youtube.com/watch?v=x4xCSVl833I',
                        source_type='UGC',
                        source_from='Олег Парастаев',
                        pulled_by='MWL',
                        source_status='Online',
                        ryg='green')
        defaults.update(kwargs)
        return super().dummy(**defaults)

    @classmethod
    def standard_attrs(cls):
        """Returns a list of all the attributes this media object is
        expected to provide, and will set from kwargs on input."""
        return Google._provides_attrs + super().standard_attrs()

class GoogleSourceClip(Google, mobs.SourceClip):
    pass
