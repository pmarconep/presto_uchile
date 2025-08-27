# PRESTO - Gemini South Changelog 
This fork is based in **PRESTO 5.1.0**

## v1.2 (To be Published)
- Added `concat_iqfits2dat.py`. This command allows to converts multiple `.fits` into one single `.dat`.
- Added `-sp` flag to `iqfits2dat.py`. This flag adds some IQUEYE constant values in the `.inf` file for the single pulse search routine of PRESTO.
- Added `-c` flag to `get_TOAs.py`. This option centers the max value of the template at bin 0. This flags forces the `-r` flag.
- Fixed `iqfits2dat.py` temporal folder overwriting if multiple instances of this command run at the same time.
- Added PS1 format for docker command prompt.
- Added `-m` flag to `get_TOAs.py` to force a `.inf` due to some bug of the command not being able to find the corresponding file.
- Minor changes and code cleaning.
- Recompiled and pushed docker image.

## v1.1
- Added TEMPO2 system wide.
- Added PSRCHIVE system wide.
- Added `iqfits2dat.py` to PRESTO, you can call it like any other PRESTO command.
- Added `-m, --inffile` flag to `get_TOAs.py` script to provide manually an `.inf` file if script is not reading it correctly.
- Minor changes.
- Recompiled and pushed docker image.

## v1.0
- Initial commit