"""Reads a list of filenames from a text file and attempts to find a
source link using a number of stock patterns.

Currently contains matchers for Getty, ShutterStock and the CL Footage
Tracker document. Uses a csv file at ~/lg_footage_tracker.csv for the
footage tracker.
"""

#!/usr/bin/env python3

import csv
import re
import requests
import sys
from urllib import request

from bs4 import BeautifulSoup

class Matcher(object):
    pattern = None
    
    def __init__(self, pattern=None, action=None, flags=re.IGNORECASE):
        if self.pattern is None:
            self.pattern = pattern
        if action is not None:
            self.action = action
        self.re = re.compile(self.pattern, flags=flags)

    def match(self, s):
        m = self.re.search(s)
        if m is not None:
            self.result = m
            return True
        return False

    def action(self):
        raise NotImplementedError()

class GettyMatcher(Matcher):
    pattern = r'^GettyImages-(\d+)'

    def action(self):
        id = self.result.group(1)
        link = 'https://www.gettyimages.com/photos/{}'.format(id)
        #link = find_link('www.gettyimages.com', '/photos/104351511?license=rf&family=creative&phrase={}&sort=best#license'.format(id), id, class_='gallery-mosaic-asset__link')
        return link

class ShutterMatcher(Matcher):
    pattern = r'^shutterstock_(\d+)'

    def action(self):
        id = self.result.group(1)
        link = 'https://www.shutterstock.com/search/{}'.format(id)
        return link

class FootageTrackerMatcher(Matcher):
    pattern = r'^(CL\d+)'

    def __init__(self, **kwargs):
        super(FootageTrackerMatcher, self).__init__(**kwargs)
        with open('/Users/creativelab/lg_footage_tracker.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            self.index(reader)

    def index(self, table):
        d = {}
        for row in table:
            id = row['ID']
            if id == '' or id == '-' or row['ID'] is None:
                continue
            if '-' in id:
                m = re.search(r'([a-zA-Z]+)(\d+)-(\d+)', id)
                name = m.group(1)
                start = m.group(2)
                end = m.group(3)
                for i in range(int(start), int(end)+1):
                    id = str(name) + str(i)
                    d[id] = row
            else:
                d[id] = row
        self.index = d

    def action(self):
        id = self.result.group(1)
        link = self.index[id]['LINK']
        return link

class QingArtMatcher(FootageTrackerMatcher):
    pattern = r'(QingArt\d+)'

class ALEMatcher(Matcher):
    pattern = r'.'

    def __init__(self, filename, **kwargs):
        super(ALEMatcher, self).__init__(**kwargs)
        rows = list()
        with open(filename) as fh:
            while next(fh) != 'Column\n':
                pass
            field_names = next(fh).split('\t')
            while next(fh) != 'Data\n':
                pass
            for line in fh:
                row = dict()
                fields = line.split('\t')
                for f, name in zip(fields, field_names):
                    row[name] = f
                rows.append(row)
        self.ale = rows

    def match(self, line):
        line = line.upper()
        # we should use a dictionary search, but need to resolve multiple entries with the same source first
        for clip in self.ale:
            if (clip['Tape'].upper() == line or clip['Source File'].upper() == line) and clip['Link'] != '':
                self.result = clip['Link']
                return True
        return False

    def action(self):
        result = self.result
        self.result = None
        return result
        
def find_link(host, urlpath, pattern='', **kwargs):
    if urlpath[0] != '/':
        urlpath = '/' + urlpath
    url = 'https://{}{}'.format(host, urlpath)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    found = soup.findAll('a', **kwargs)
    for a in found:
        if pattern in a['href']:
            link = a['href']
            if 'http' not in link:
                link = host + link
            return link

def process(line, matchers):
    for m in matchers:
        if m.match(line):
            line = m.action()
            break
    if isinstance(line, str):
        line = line.strip()
    return line

def main(args):
    infile = args[0]
    matchers = [ GettyMatcher(), ShutterMatcher(), FootageTrackerMatcher(), QingArtMatcher() ]
    with open(infile) as fh_in:
        for line in fh_in:
            line = process(line, matchers)
            print(line)
