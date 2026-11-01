# PRESTO - Gemini South Changelog 
This fork is based in **PRESTO 5.2.0.dev**

## v1.5
- **Fixed "gs" Goldstone collision**: stock tempo2 defines `GOLDSTONE gs`;
  tempo2 resolves the FIRST match in observatories.dat, so all `gs` TOAs
  (Iqueye@Gemini-S) were barycentered at **Goldstone** instead of Gemini South.
  Goldstone short name renamed to `goldstone` at docker build time.
- Build now FAILS if any tempo2 observatory short name is duplicated
  (same failure mode: silently barycenters at the wrong site).
- obsys.dat: added GB140 (w/G1), FAST (j/FA), WSRT (l/WT), ATA (n/AT) —
  previously referenced by PRESTO code with codes that did not exist or
  belonged to other sites.
- polycos.c: GB43m 'a'->'w', ATA 's'->'n', FAST 'k'->'j' (old codes silently
  resolved to IAR1, SHAO 65m and CPT respectively).
- get_TOAs.py: TEMPO1 `scopes` dict updated to this fork's obsys.dat
  ('LWA1':'x' would have resolved to Gemini-S!, 'FAST':'k' to CPT,
  'IRAM':'s' to SHAO, 'VLA':'c' to IAR1R). Added ARO/Gemini-S/CPT/IAR entries.
- python/presto/polycos.py + barycenter.py: telescope tables aligned with
  this fork's obsys.dat; added ARO/AZ, Gemini-S/GS, CPT/CP, IAR antennas
  and the new GB140/FAST/WSRT/ATA entries.
- FAQ.md: fixed sign of the X coordinate in the Gemini South example line.

## v1.3
- Merged with PRESTO 5.2.0.dev (02-04-2026)
- Added IAR1 for folding.
- Minor fixes

## v1.2.1
- Added IAR1, IAR2, IAR1R and IAR2R to TEMPO, TEMPO2 and PRESTO.
- Made the default option to NOT barycenter in `iqfits2dat.py`
- Minor fixes and changes.

## v1.2
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
