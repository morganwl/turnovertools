#!/usr/bin/env python3
"""Shared user interface functions for turnovertools."""

import os

class Input(object):
    """Organizes various input objects."""

    def __init__(self, inputfile, outputfile=None, outputdir=None, **kwargs):
        if os.path.isdir(inputfile):
            self.parse_directory(inputfile, **kwargs)
        else:
            self.inputfile = inputfile
            self.inputdir = os.path.abspath(os.path.dirname(inputfile))
        if outputfile is None:
            self.gen_outputs(outputdir)
        else:
            self.outputdir = os.path.abspath(os.path.dirname(outputfile))
            self.outputfile = outputfile
            self.outputbase = os.path.basename(outputfile)

    def parse_directory(self, inputfile, **kwargs):
        inputfile.rstrip('/')
        self.inputdir = os.path.abspath(inputfile)
        input_edls = list()

        for file in os.listdir(self.inputpath):
            if file.lower().endswith('.edl'):
                inputfile_edls.append(os.path.join(basepath, file))

        if not input_edls:
            input_edls = [ inputfile ]

    def gen_outputs(self, outputdir):
        if outputdir is None:
            outputdir = self.inputdir
        self.outputdir = outputdir

        if self.inputfile is None:
            basename = os.path.basename(self.inputdir)
        else:
            basename = os.path.splitext(
                os.path.basename(self.inputfile))[0]

        self.output_csv = os.path.join(self.outputdir, basename + '.csv')
        self.output_ale = os.path.join(self.outputdir, basename + '.ale')
        self.output_edl = os.path.join(self.outputdir, basename + '.edl')
        self.output_base = basename

