"""Classes of media objects (mobs) for internal representation and
manipulation. Functions for converting to and from various file formats
should be handled by adapters submodule.

All objects can be initialized with kwargs for all their attributes,
and have a to_dict() method for exporting their entire state. Mobs can
also be initialized from other mobs."""

from .timecode import Timecode
from .mob import Mob, Clip
from .event import *
from .vfxevent import VFXEvent
from .source_clip import SourceClip
