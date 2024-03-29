#!/usr/bin/env python3

import logging
import os
import sys
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from turnovertools import xmlparser, xmlobjects, mediaobject

TEST_FILES = os.path.join(TEST_DIR, 'test_files')
TEST_XML_COMPLEX = os.path.join(TEST_FILES, 'R2-v29_Flattened.xml')
