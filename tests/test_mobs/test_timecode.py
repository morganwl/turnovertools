"""Tests mobs.Timecode, a revised child of the timecode.Timecode class."""

import unittest

from timecode import Timecode

import turnovertools.mediaobjects as mobs

class TestMobsTimecode(unittest.TestCase):
    """The mobs.Timecode class should be a pass-through to
    timecode.Timecode, with some better generation functionality."""

    def setUp(self):
        pass

    def test_timecode_creation_with_string(self):
        """Checks to see that mobs.Timecode and Timecodes created with
        the same strings return the same values."""
        timecode = Timecode(24, '01:00:00:00')
        mobs_timecode = mobs.Timecode(24, '01:00:00:00')
        self.assertEqual(mobs_timecode, timecode)
        self.assertEqual(mobs.Timecode('23.98', '03:00:00:00'),
                         Timecode('23.98', '03:00:00:00'))

    def test_2398_equals_23976(self):
        """Checks that framerates of 23.976 and 23.98 (two names for
        24fps pulldown timecode) are interpeted the same way."""
        self.assertEqual(mobs.Timecode('23.98', '05:00:00:00'),
                         mobs.Timecode('23.976', '05:00:00:00'))
        self.assertEqual(mobs.Timecode('23.98', '05:00:00:00').frames,
                         mobs.Timecode('23.976', '05:00:00:00').frames)
        self.assertEqual(mobs.Timecode(23.98, '05:00:00:00'),
                         mobs.Timecode(23.976, '05:00:00:00'))
        self.assertEqual(mobs.Timecode(23.98, '05:00:00:00').frames,
                         mobs.Timecode(23.976, '05:00:00:00').frames)

    def test_2398_frames_equals_24_frames(self):
        """Checks that timecodes with true 24 and pulldown 24 framerates
        have the same number of frames for any given timecode."""
        tc24 = mobs.Timecode(24, '01:00:00:00')
        tc2398 = mobs.Timecode(23.98, '01:00:00:00')
        for addend in range(0, 24 * 60 * 60 * 22, 993):
            self.assertEqual((tc24 + addend).frames,
                             (tc2398 + addend).frames)

    def test_pulldown_framerates_arithmetic(self):
        """Checks that operations on mobs.Timecode objects with
        framerate 23.98 have the same result as operations on objects
        with framerate 24."""
        tc24 = mobs.Timecode(24, '01:00:00:00')
        tc2398 = mobs.Timecode(23.98, '01:00:00:00')
        for addend in range(0, 24 * 60 * 60 * 22, 163):
            self.assertEqual(str(tc24 + addend),
                             str(tc2398 + addend))

    def test_timecode_creation_with_timecode(self):
        """Checks to see that a mobs.Timecode created with a Timecode
        returns the same value as the original Timecode."""
        timecode = Timecode(24, '01:10:10:23')
        mobs_timecode = mobs.Timecode(24, timecode)
        self.assertEqual(mobs_timecode, timecode)

    def test_timecode_creation_with_timecode_and_no_framerate(self):
        """Cast a Timecode object to a mobs.Timecode object directly, without
        specifying a framerate (since the Timecode object already has
        one)."""
        timecode = Timecode(24, '01:10:10:23')
        mobs_timecode = mobs.Timecode(timecode)
        self.assertEqual(mobs_timecode, timecode)

    def test_timecode_from_set(self):
        """Return a set of timecodes with the same framerate."""
        framerate = 24
        str_timecodes = ('01:10:10:23', '01:10:12:23', '01:10:15:23')
        timecodes = (Timecode(framerate, str_timecode) for str_timecode in str_timecodes)
        mobs_timecodes = mobs.Timecode.from_set(framerate, str_timecodes)
        for mobs_timecode, timecode in zip(mobs_timecodes, timecodes):
            self.assertEqual(mobs_timecode, timecode)

    def test_arithmetic_returns_mobs_timecode(self):
        """Arithmetic operations should return object of the same class, not
        the parent class."""
        timecode = mobs.Timecode(24, '01:00:00:00')
        other_timecode = mobs.Timecode(24, '00:00:30:00')
        other_int = 721
        self.assertIsInstance(timecode + other_timecode, type(timecode))
        self.assertIsInstance(timecode + other_int, type(timecode))
        self.assertIsInstance(timecode - other_timecode, type(timecode))
        self.assertIsInstance(timecode - other_int, type(timecode))
        self.assertIsInstance(timecode * other_timecode, type(timecode))
        self.assertIsInstance(timecode * other_int, type(timecode))
        self.assertIsInstance(timecode // other_timecode, type(timecode))
        self.assertIsInstance(timecode // other_int, type(timecode))

    def test_timecode_division(self):
        """Need to think through what a **desirable** behavior for Timecode
        division would be, based on the ways in which Timecode stores frame
        numbers."""
        timecode = mobs.Timecode(24, '01:00:00:00')
        expected_result = mobs.Timecode(24, '00:29:59:23')
        self.assertEqual(timecode // 2, expected_result)

    def test_timecode_exception_on_mismatched_framerates(self):
        """Creates a mobs.Timecode with an explicit framerate, but
        passes a Timecode object with a different framerate."""
        timecode = Timecode(30, '01:10:10:23')
        with self.assertRaises(ValueError):
            mobs.Timecode(24, timecode)
