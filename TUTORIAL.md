# IQUEYE PRESTO Tutorial

We have a couple of workflows according to what are you trying to do. For this, there are a lot of tools installed in the docker image. The softwares present are:
 - PRESTO v5.0.3
 - TEMPO  v13.103
 - TEMPO2 v2025.01.2
 - PSRCHIVE v2025-05-13

 If you build the image yourself, it will pull the latest software version available.

## Transforming IQUEYE .fits to .dat
The first step is to make a readeable format for PRESTO. For this, inside the container, we use `iqfits2dat.py`. We need to provide the template `.inf` file, the output path, and the `.fits` file. For PRESTO compatibility issues, we need to select the `bin time` fo the light curve right now. I recommend to go low, as you can always undersample, but you can't oversample. However, if you use a `dt` too small, the files will be large, and the process slower. It will depend in the amount of counts that file has. 

- Example: ``iqfits2dat.py -t path/to/template.inf -o path/to/outfile -dt 1e-6 path/to/infile.fits``

Useful flags:
 - `-nobary`; by default, this command tries to barycenter the data using `prepdata` command from PRESTO. This flag will override this. Also, if the IQUEYE `.fits` are already barycentered, it will automatically skip this step.
 - `--pulsar_name`, `-ra`, `-dec`; This command needs the RA and DEC of the source. In the script there is a small dictionary with all the already observed targets from the 2025-02 IQUEYE run. If for some reason, you need to open another target, please provide the RA, DEC and Target name manually. 
 
TODO: reference this into a file of targets so they can be added on hot. 

Note: this command is programmed only for IQUEYE `.fits`, both barycentered or not. Any other `.fits` will likely fail or produce wrong results.


## Searching for a signal

## Folding

## Building a .par file

## Folding with .par file



# NICER PRESTO Tutorial
