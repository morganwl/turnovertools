# turnovertools
tools for processing Avid Media Composer turnovers

Development is erratic, chasing around to follow actual tasks on the job.

## Changelog

### 0.0.6 05.06.2020

- To-Do:
  - Write full testsuite for ryglist
  - Refactor more generalized ryglist
  - Connect ryglist to FileMaker database
  - Tie FileMaker tables together
  - Fix missing umids in mxfdb
  - Fix MXF/1 refresh bug in mxfdb
  - Migrate mxfdb to using MediaFile mob

### 0.0.5 04.15.2020

- Changes:
  - insert_umid script allows finding and inserting thumbnails in source table
  - FileMaker source table support
  - created MediaFile and SourceClip mobs
  - fixed bugs in Timecode mob
  - renamed xml2ryg to ryglist

- To-Do:
  + Fix or flag failing tests
  - Clean up command line interface for ale2csv and insert_umid

- To-Do in Next Version:
  - Write full testsuite for ryglist
  - Refactor more generalized ryglist
  - Connect ryglist to FileMaker database
  - Tie FileMaker tables together
  - Fix missing umids in mxfdb
  - Fix MXF/1 refresh bug in mxfdb
  - Migrate mxfdb to using MediaFile mob

### 0.0.4 04.15.2020

- added VFX list support
  - read EDLs and extract vfx list based on markers
  - create pull EDLs and ALEs
  - create VFX reference with appropriate burnins
  - limited integration with FileMaker

### 0.0.3 02.03-2020

- (NONE OF THIS HAPPENED)
  - build and use source tables
    - build source table from ale, xml or edl
    - fill in metadata from existing source table for xml and edl
      imports
    - output source table in human readable format
    - allow editing of source table

- Stretch
  - Explore using MobID in XML or AAF to find source media on drive
  - Add AAF support
  - SQLAlchemy support
  - Flask viewer support

### 0.0.2 - 01.29.2020

- preliminary xml2ryg support
  - output CSV per ryg specs
    - includes sequence number in timecode order
  - output poster-frames for each event
    - poster frames are numbered and labeled exactly matching event
  - output video for each event
    - video labeled exactly matching event
  - added command line syntax

- To-Do:
  - multiple framerates
  - some sort of configuration file
  - guess reel numbers and media file locations

### 0.0.1 - 01.12.2020

- Basic support for parsing Avid XML sequences into python objects
  - Parse sequence, containing tracks, containing events
  - Access custom attributes of XML Events
