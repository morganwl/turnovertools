# turnovertools
tools for processing Avid Media Composer turnovers

## Changelog

### 0.0.2 - 01.29.2019

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

- Stretch
  - Explore using MobID in XML to find source media on drive
  - Add AAF support

### 0.0.1 - 01.12.2019

- Basic support for parsing Avid XML sequences into python objects
  - Parse sequence, containing tracks, containing events
  - Access custom attributes of XML Events
