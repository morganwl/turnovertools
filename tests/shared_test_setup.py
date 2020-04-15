"""Shared setup and functions for testing turnovertools."""

import os
import sys

USER_HOME = os.path.expanduser("~")
TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

def swap_key(dictionary, old, new):
    """Swaps an old key for a new key in a dictionary. If the new key did not
    exist, deletes the old key from the dictionary."""
    temp_val = dictionary.get(new)
    dictionary[new] = dictionary[old]
    if temp_val is None:
        del dictionary[old]
    else:
        dictionary[old] = dictionary[new]

def get_scripts(*args):
    return os.path.join(MAIN_DIR, 'scripts', *args)

def get_private_test_files(*subpackage):
    """Accepts a subpackage name and returns the private test file directory
    for that package. These are test files stored outside of the project
    directory for total protection against git tracking."""
    return os.path.join(USER_HOME, 'private_test_files', *subpackage)
