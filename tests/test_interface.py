#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile
import unittest

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from turnovertools import interface

class TestInput(unittest.TestCase):
    def setUp(self):
        pass

    def test_inputfile_single(self):
        """Checks to see that the inputfile attribute of input object matches
        the supplied inputfile parameter."""
        inputfile = './test.csv'
        input = interface.Input(inputfile)
        self.assertEqual(input.inputfile, inputfile)

    def test_implied_outputfiles(self):
        inputfile = os.path.join(TEST_DIR, 'test_dir', 'test.csv')
        expected_output_csv = os.path.join(TEST_DIR, 'test_dir', 'test.csv')
        expected_output_ale = os.path.join(TEST_DIR, 'test_dir', 'test.ale')
        expected_output_edl = os.path.join(TEST_DIR, 'test_dir', 'test.edl')
        input = interface.Input(inputfile)
        self.assertEqual(input.output_csv, expected_output_csv)
        self.assertEqual(input.output_ale, expected_output_ale)
        self.assertEqual(input.output_edl, expected_output_edl)
