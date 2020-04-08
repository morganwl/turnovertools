import csv
import logging
import os
import sys
import tempfile
import unittest

TEST_DIR = os.path.dirname(__file__)
MAIN_DIR = os.path.join(TEST_DIR, os.pardir)

sys.path.insert(0, MAIN_DIR)

from scripts import xml2ryg
from turnovertools import mediaobject

TEST_FILES = os.path.join(TEST_DIR, 'test_files')
TEST_XML_COMPLEX = os.path.join(TEST_FILES, 'R2-v29_Flattened.xml')
EXPECTED_XML_COMPLEX = os.path.join(TEST_FILES, 'R2-v29_Flattened_expected_output.csv')
TEST_XML_COMPLEX_VIDEO = '/Volumes/LookingGlass1015-AS08_1/Avid MediaFiles/MXF/Creative’s Mac Pro.1/R2-v29,Video Mixdo6A90267CV.mxf'

EXPECTED_CSV_COLUMNS = ['Number', 'Clip Name' , 'Tape Name',
                        'Link', 'Footage Type',
                        'Footage Source', 'Rec Start',
                        'Rec End', 'Source Start',
                        'Source End']

@unittest.skip('Legacy xml2ryg no longer included, but keeping testsuites for reference.')
class TestXml2RygCLI(unittest.TestCase):
    def setUp(self):
        self.test_xml = TEST_XML_COMPLEX
        self.expected_csv = EXPECTED_XML_COMPLEX
        self.expected_columns = EXPECTED_CSV_COLUMNS
        self.test_video = TEST_XML_COMPLEX_VIDEO
        # reserve a temporary filename and open it as read-only for
        # later verification
        self.temp_output = tempfile.NamedTemporaryFile(mode='r', newline='',
                                                       suffix='.csv')

    def tearDown(self):
        # delete temporary file
        self.temp_output.close()

    def test_video_output(self):
        with tempfile.TemporaryDirectory() as video_dir:
            xml2ryg.main(self.test_xml, self.temp_output.name,
                         videofile=self.test_video,
                         videooutput=video_dir)

            # read in the csv output
            reader = csv.reader(self.temp_output)
            columns = next(reader)
            
            for file in sorted(os.listdir(video_dir)):
                with self.subTest(file=file):
                    # test that file names match csv rows                   
                    row = next(reader)
                    num, clip_name = file.split('_', 1)
                    self.assertEqual(int(num), int(row[0]))
                    self.assertEqual(clip_name, row[1] + '.mp4')

    def test_frame_output(self):
        # create a temporary image output directory
        with tempfile.TemporaryDirectory() as frame_dir:
            xml2ryg.main(self.test_xml, self.temp_output.name,
                         videofile=self.test_video,
                         frameoutput=frame_dir)

            # read in the csv output
            reader = csv.reader(self.temp_output)
            columns = next(reader)

            for file in sorted(os.listdir(frame_dir)):
                with open(os.path.join(frame_dir, file), 'rb') as frame:
                    with self.subTest(file=file):
                        # test that files are complete jpeg files
                        beginning = frame.read(3)
                        frame.seek(-2, 2)
                        end = frame.read(2)
                        self.assertEqual(beginning, b'\xff\xd8\xff')
                        self.assertEqual(end, b'\xff\xd9')
                        
                        # test that file names match csv rows
                        row = next(reader)
                        num, clip_name = file.split('_', 1)
                        self.assertEqual(int(num), int(row[0]))
                        self.assertEqual(clip_name, row[1] + '.jpg')

    def test_csv_expected_output(self):
        # read in expected csv output
        with open(self.expected_csv, newline='') as expected_output_file:
            reader = csv.reader(expected_output_file)
            expected_columns = next(reader)
            expected_rows = list(reader)

        # call xml2ryg with the path of our temporary file as the
        # output option
        xml2ryg.main(self.test_xml, self.temp_output.name)
        
        # compare column output to expected columns
        reader = csv.reader(self.temp_output)
        output_columns = next(reader)
        self.assertEqual(output_columns, expected_columns)

        # read in output rows
        output_rows = list(reader)
        
        # compare output rows to expected rows, one column at a time
        for column_number, column in enumerate(expected_columns):
            
            # temporarily skip signature column
            if column == 'signature':
                continue
            
            with self.subTest(column=column):
                for row_number, row in enumerate(output_rows):
                    # print(column, row)
                    self.assertEqual(row[column_number],
                                     expected_rows[row_number][column_number])

@unittest.skip('Legacy xml2ryg no longer included, but keeping testsuites for reference.')
class TestXml2rygInternals(unittest.TestCase):
    def setUp(self):
        self.input = TEST_XML_COMPLEX
        self.events = xml2ryg.events_from_xml(TEST_XML_COMPLEX)

    def test_input_xml(self):
        events = xml2ryg.events_from_xml(TEST_XML_COMPLEX)
        for i, e in enumerate(events):
            with self.subTest(i=i):
                self.assertIsInstance(e, mediaobject.Event)

    def test_sort_events_by_timecode(self):
        xml2ryg.sort_by_tc(self.events)
        sorted_events = self.events
        previous_timecode = ''
        previous_track = ''
        for i, e in enumerate(sorted_events):
            this_timecode = e.rec_start_tc
            this_track = e.parent.track_name
            with self.subTest(i=i):
                self.assertGreaterEqual(this_timecode, previous_timecode)
                if this_timecode == previous_timecode:
                    self.assertGreater(this_track, previous_track)
            previous_timecode = this_timecode
            previous_track = this_track

    def test_remove_filler(self):
        expected_filler_indices = [1, 90, 257, 273, 276, 279, 287, 293, 
                                   297, 299, 302, 307, 309, 311, 313, 
                                   315, 320, 322, 323, 324]
        for i, e in enumerate(self.events):
            remove_filler = xml2ryg.remove_filler(e)
            if remove_filler is None and i not in expected_filler_indices:
                with self.subTest(i=i):
                    self.fail('Unexpected event marked as filler.')
            elif remove_filler is not None and i in expected_filler_indices:
                with self.subTest(i=i):
                    self.fail('Expected filler event not marked as filler.')

    @unittest.skip('Feature postponed')
    def test_compare_existing(self):
        self.fail('Unwritten test.')

    def test_guess_metadata(self):
        for e in self.events:
            xml2ryg.guess_metadata(e)

    @unittest.skip('Feature postponed')
    def test_include_update_sheet(self):
        self.fail('Unwritten test.')

    @unittest.skip('Potential rewrite')
    def test_csv_output(self):
        output_columns = ['event_num', 'clip_name', 'reel', 'link', 'NOTES',
                          'Footage Type', 'Footage Source', 'rec_start_tc',
                          'rec_end_tc', 'src_start_tc', 'src_end_tc', 'signature']
        r0_expected_values = ['Event Number', 'Clip Name' , 'Tape Name',
                              'Link,Footage Type',
                              'Footage Source', 'Rec Start',
                              'Rec End', 'Source Start',
                              'Source End', 'signature']
        r6_expected_values = ['3', 'GOMES_Acam_Raw_Tk1', 'A007C005_190425_R0FA',
                              '', '', '', '01:00:00:01', '01:00:08:20',
                              '10:44:00:03', '10:44:08:22',
                              'A007C005_190425_R0FA:e2683:e2756']
        events = xml2ryg.sort_by_tc(self.events)
        events = xml2ryg.process_events(events)
        output_csv(events, output_columns, temp_file)
        self.fail('Unwritten test.')

    @unittest.skip('Potential rewrite')
    def test_frame_output(self):
        self.fail('Unwritten test.')

    @unittest.skip('Potential rewrite')
    def test_video_output(self):
        self.fail('Unwritten test.')
