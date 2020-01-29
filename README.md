# turnovertools
tools for processing Avid Media Composer turnovers

## Changelog

### 0.0.2 - 01.29.2019

- Planned features
  - xml2ryg
    - output CSV per ryg specs
	  - include sequence number in timecode order
	- output post-frames for each event
	  - output names should match sequence number of csv event
	- output video for each event

- Stretch
  - Explore using MobID in XML to find source media on drive
  - Add AAF support

### 0.0.1 - 01.12.2019

- Basic support for parsing Avid XML sequences into python objects
  - Parse sequence, containing tracks, containing events
  - Access custom attributes of XML Events
