"""Convert Avid ALE into a csv file for import into FileMaker. Use mobs
standard attribute names as field names. Optionally create csv in a
temporary file and output the location to STDOUT."""

# - Read ALE rows from input as dict-like objects.
# - Translate dict keys to mobs attribute names.
# - [We can bypass the actual creation of mobs and just output straight
#    to csv, or we can convert to mobs first. Keep it simple for now.]
# - Optionally create NamedTemporaryFile
# - Output csv
# - Output filename to STDOUT

# Stretch:
# - Output sources directly into FileMaker, preferably using an "import"
#   table, from which the user can confirm before committing to the
#   master source database
# - Output poster frames using mxf database

import unittest

import tests.shared_test_setup

from scripts import ale2csv

class TestALE2CSV(unittest.TestCase):
    """Read in an ALE file."""

    def test_ale_input(self):
        """Input a legal ALE and get a list of dictionaries matching
        mob attribute names."""

    def test_temporary_output(self):
        """--temp option should create a temporary file and output the
        name to STDOUT."""

    def test_output_csv(self):
        """Inputs a dictionary in mob form and expects a csv."""
