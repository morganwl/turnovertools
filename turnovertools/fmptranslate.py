"""
fmptranslate.py

Imports and exports various MediaObjects from and to format understood
by FMP.
"""

import csv

lookup = { '' : '',
    }

def read_csv(inputfile, mobtype):
    """
    Reads a CSV and returns a MediaObject of type mobtype.
    """
    with open(inputfile, newline='') as fh:
        reader = csv.DictReader(fh)
        

def write_csv():
    pass
