[![PINT on ASCL](https://img.shields.io/badge/ascl-1107.017-blue.svg)](https://ascl.net/1107.017)

# IQUEYE at Gemini South Fork

PRESTO is a large suite of pulsar search and analysis software developed primarily by Scott Ransom mostly from scratch, and released under the GPL (v2). It was primarily designed to efficiently search for binary millisecond pulsars from long observations of globular clusters (although it has since been used in several surveys with short integrations and to process a lot of X-ray data as well). It is written primarily in ANSI C, with many of the recent routines in Python. According to Steve Eikenberry, PRESTO stands for: PulsaR Exploration and Search TOolkit!

## About this fork

This fork is based on **PRESTO 5.1.0**. This brings some modifications so all the software works with Gemini South and IQUEYE data. Plus, some scripts for treating some particulars about IQUEYE data.

### Extra functions
- Gemini South, ARO and IAR telescopes added.
- Custom docker file with `psrchive` and `tempo2` added.

### Extra commands
- **fits2dat.py**: This can transform *.fits* to *.dat* baricentering in the process.

## About PRESTO:
PRESTO is written with portability, ease-of-use, and memory efficiency in mind, it can currently handle raw data from the following pulsar machines or formats:

 * PSRFITS search-format data (as from GUPPI at the GBT, PUPPI and the Mock Spectrometers at Arecibo, and much new and archived data from Parkes)
 * 1-, 2-, 4-, 8-, and 32-bit (float) filterbank format from SIGPROC
 * A time series composed of single precision (i.e. 4-byte) floating point data (with a text ".inf" file describing it)
 * Photon arrival times (or events) in ASCII or double-precision binary formats

Notice that the following formats which *used* to be supported are not:

 * Wideband Arecibo Pulsar Processor (WAPP) at Arecibo
 * The Parkes and Jodrell Bank 1-bit filterbank formats
 * SPIGOT at the GBT
 * Berkeley-Caltech Pulsar Machine (BCPM) at the GBT

If you need to process them, you can either checkout the "classic" branch of PRESTO (see below), which is not being actively developed. Or you can use DSPSR to convert those formats into SIGPROC filterbank or (even better) PSRFITS search format. You can grab DSPSR [here](http://dspsr.sourceforge.net).  If you *really* need to get one of these machines working in modern PRESTO, let me know and we can probably make it happen.

The software is composed of numerous routines designed to handle three main areas of pulsar analysis:

1. Data Preparation: Interference detection (`rfifind`) and removal (`zapbirds` and `pfdzap.py`), de-dispersion (`prepdata`, `prepsubband`, and `mpiprepsubband`), barycentering (via TEMPO).
2. Searching: Fourier-domain acceleration and jerk (`accelsearch`), single-pulse (`single_pulse_search.py`), and phase-modulation or sideband searches (`search_bin`).
3. Folding: Candidate optimization (`prepfold` and `fourier_fold.py`) and Time-of-Arrival (TOA) generation (`get_TOAs.py`).
4. Misc: Data exploration (`readfile`, `exploredat`, `explorefft`), de-dispersion planning (`DDplan.py`), date conversion (`mjd2cal`, `cal2mjd`), tons of python pulsar/astro libraries, average pulse creation and flux density estimation (`sum_profiles.py`), and more...
5. Post Single Pulse Searching Tools: Grouping algorithm (`rrattrap.py`), Production and of single pulse diagnostic plots (`make_spd.py`, `plot_spd.py`, and `waterfaller.py`).

Many additional utilities are provided for various tasks that are often required when working with pulsar data such as time conversions, Fourier transforms, time series and FFT exploration, byte-swapping, etc.

**References**: The Fourier-Domain acceleration search technique that PRESTO uses in the routine `accelsearch` is described in [Ransom, Eikenberry, and Middleditch (2002)](https://ui.adsabs.harvard.edu/abs/2002AJ....124.1788R/abstract), the "jerk" search capability is described in [Andersen & Ransom (2018)](https://ui.adsabs.harvard.edu/abs/2018ApJ...863L..13A/abstract), and the phase-modulation search technique used by `search_bin` is described in [Ransom, Cordes, and Eikenberry (2003)](https://ui.adsabs.harvard.edu/abs/2003ApJ...589..911R/abstract). Some other basic information about PRESTO can be found in my [thesis](http://www.cv.nrao.edu/~sransom/ransom_thesis_2001.pdf).

**Support/Docs**:  I may eventually get around to finishing the documentation for PRESTO (or not), but until then you should know that each routine returns its basic usage when you call it with no arguments. I am also willing to provide limited support via email (see below). And make sure to check out the `FAQ.md`!

**Tutorial**: There is a tutorial in the "docs" directory which walks you through all the main steps of finding pulsars using PRESTO.

## Getting it: 
The PRESTO source code is released under the GPL and can be browsed or gotten from here in many different ways (including zipped or tar'd or via git). If you are too lazy to read how to get it but have git on your system do:

    git clone git://github.com/scottransom/presto.git

To update it on a regular basis do

    cd $PRESTO
    git pull

and then re-build things in $PRESTO.

For more detailed installation instructions, see [INSTALL.md](https://github.com/scottransom/presto/blob/master/INSTALL.md).

If you want the "classic" branch, do the following:

    git clone git://github.com/scottransom/presto.git
    cd presto
    git checkout -b classic origin/classic

then build as per the (old) INSTALL file.

### Docker

This dockerfile is based on `alex88ridolfi/presto5:latest`

Some software may be hard to install and it is best to use it within a docker container. To accomplish so we will be relaying on the presto software and community. First pull the docker container and run it, once within it you can run commands as if you were in a normal terminal. Beware that using docker may expose your entire local files to a sudo user within the container, capable of removing or modifying files.

In addition, whatever change made within docker will be erased after the container is stopped or removed. The only changes that will exists are within the mounted volumes (using the `-v` flag).

We built our own docker container to make it compatbile with IQUEYE and Gemini South. There are some telescopes added, and some minimal modifications to PRESTO for everything to work. If you plan to add new telescopes, we recommend you build your own image with this dockerfile. If you just want an out of the box, and don't plan to modify enything, you can just pull our presto image.

IMPORTANT NOTE: The other modification to this image is that an ssh server is started on the docker container, this way you can forward GUI apps from the docker container to your own screen fairly easy. However, in the image, my own (Pascual Marcone) public ssh key is written there. For your ease of mind, just delete it from `/root/.ssh/authorized_keys` and add your own so you can ssh to the docker file.

#### Build your own image

First, we recommend you do some modifications to the dockerfile before running the commands. 

- Check that every linux tool you use is in the line `RUN apt install ...`
- Same for python libraries, check `RUN pip install ...`
- In the SSH SETUP section, change the public key for the one you will be using to ssh in. The ssh must happend from inside the same machine
- If you want to add, modify or delete some telescopes, you need to add it to the line that is modifying the tempo/obsys.dat. You also need to modify some lines in PRESTO, you cna use the commands in the dockerfile as template. NOTE: please refer to [PRESTO FAQ](https://github.com/scottransom/presto/blob/master/FAQ.md#how-do-i-add-a-new-telescope-into-presto).

We recommend to do not modify anything else unless you know what you are doing.

Now, to build this our own docker container use the following commands:

```zsh
docker build -f path/to/dockerfile -t presto-gs . --load

docker run -itd -v /local/path1:/path1 -v /local/path2:/path2 -p 2150:22 --name presto-container presto-gs
```

If you added your ssh public key into the dockerfile, you should be able to ssh

```zsh
ssh -Y root@your_ip -p 2150
```
You can setup for easy ssh with 

```zsh
Host presto
        Hostname 172.17.31.85
        Port 2150
        user root
        ForwardX11 yes
        ForwardX11Trusted yes

ssh presto
```

#### Pull existing image

For the new chip MacOS systems the build routine may not work. In this case, use the following commands to pull the image and run it:

```zsh
docker pull pmarcone/presto-gs:v1.0

# check whether the image is there
docker images

# starting docker container
docker run -itd -v /local/path1:/path1 -v /local/path2:/path2 -p 2150:22 --name presto-container pmarcone/presto-gs:v1.0
```
You will need however to setup manually your public ssh key.

```zsh
docker exec -it presto-container bash

echo "your_public_key" >> /root/.ssh/authorized_keys`
```

Now you can ssh in with the instructions in the Build your own image section.

**Code contributions and/or patches to fix bugs are most welcome!**

### Final Thoughts:
Please let me know if you decide to use PRESTO for any "real" searches, especially if you find pulsars with it!

And if you find anything with it, it would be great if you would cite either my thesis or whichever of the three papers listed above is appropriate.

Also note that many people are now also citing software using the ASCL, in addition to the relevant papers: [PRESTO is there!](https://www.ascl.net/1107.017).

Thanks!

### Acknowledgements:
Big thanks go to Steve Eikenberry for his help developing the algorithms, Dunc Lorimer and David Kaplan for help with (retired) code to process BCPM, SCAMP, and Spigot data, among other things, Jason Hessels and Patrick Lazarus for many contributions to the Python routines, and (alphabetical): Bridget Andersen, Anne Archibald, Cees Bassa, Matteo Bachetti, Slavko Bogdanov, Fernando Camilo, Shami Chatterjee, Kathryn Crowter, Paul Demorest, Paulo Freire, Nate Garver-Daniels, Chen Karako, Mike Keith, Maggie Livingstone, Ryan Lynch, Erik Madsen, Bradley Meyers, Gijs Molenaar, Timothy Olszanski, Chitrang Patel, Paul Ray, Alessandro Ridolfi, Paul Scholz, Maciej Serylak, Ingrid Stairs, Kevin Stovall, Nick Swainston, and Joeri van Leeuwen for many comments, suggestions and patches!

Scott Ransom <sransom@nrao.edu>
