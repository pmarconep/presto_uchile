# PRESTO - Gemini South Changelog 
This fork is based in **PRESTO 5.0.3**

## v1.2
- Added `-sp` flag to `iqfits2dat.py`. This flag adds some IQUEYE constant values in the `.inf` file for the single pulse search routine of PRESTO.

## v1.1
- Added TEMPO2 system wide.
- Added PSRCHIVE system wide.
- Added `iqfits2dat.py` to PRESTO, you can call it like any other PRESTO command.
- Added `-m, --inffile` flag to `get_TOAs.py` script to provide manually an `.inf` file if script is not reading it correctly.
- Minor changes.
- Recompiled and pushed docker image.

## v1.0
- Initial commit