#!/usr/bin/env python
import subprocess
import shlex
import os
import sys
import numpy as np
import pathlib
import fitsio
import shutil
import argparse

def usage():
    sys.stderr.write("""
usage: fits2dat.py -t TEMPLATE.inf -o OUTPUT_DIR -dt BIN_TIME [options] INPUT_FILE

Options:
  -h, --help                : Display help message and exit
  -t, --template TEMPLATE   : Path to the template .inf file (required)
  -o, --output_dir DIR      : Output directory for barycentered data (required)
  -dt, --bin_time BIN_TIME  : Bin time wanted for the pulsar (required)
  -ra, --ra RA              : Right Ascension (RA) of the pulsar (e.g., 12:31:11.307)
  -dec, --dec DEC           : Declination (DEC) of the pulsar (e.g., -45:10:35.15)
  -nobary, --no_bary        : Do not barycenter the data
  --name NAME               : Name to use in PRESTO logs (default: "Astrolab")
  INPUT_FILE                : Path to input .fits file (required)

Description:
  Converts IQUEYE FITS files to PRESTO .dat format, optionally barycentering the data.
  The script extracts time events from the FITS file, writes an events file, creates
  and updates a PRESTO .inf file, and generates a .dat file. If barycentering is not
  disabled and the FITS file is not already barycentered, it will barycenter the .dat
  file using PRESTO's prepdata.

Examples:
  fits2dat.py -t template.inf -o ./output -dt 0.001 --name "Pascual Marcone" data/psrj1231_20220101.fits
  fits2dat.py -t template.inf -o ./output -dt 0.001 -ra 12:31:11.307 -dec -14:11:43.63 data/psrj1231_20220101.fits

Notes:
  - If RA and DEC are not provided, the script will attempt to look them up for known pulsars at IQUEYE run.
  - The output files will be placed in the specified output directory.
  - Temporary files are cleaned up automatically.
""")

def cmd(command):
    try:
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"stderr: {e.stderr}")
        return None

def copy_inf_file(source_path, destination_folder, new_name=None):
    """
    Copy a .inf file to another folder, optionally renaming it.

    Args:
        source_path: Path to the source .inf file
        destination_folder: Path to the destination folder
        new_name: Optional new name for the copied file (including extension)

    Returns:
        bool: True if the file was copied successfully, False otherwise
    """
    try:
        # Ensure the destination folder exists
        os.makedirs(destination_folder, exist_ok=True)
        
        # Determine the destination file name
        destination_file_name = new_name if new_name else os.path.basename(source_path)
        
        # Construct the destination path
        destination_path = os.path.join(destination_folder, destination_file_name + '.inf')
        
        # Copy the file
        shutil.copy(source_path, destination_path)
        
        # print(f"Copied {source_path} to {destination_path}")
        return True
    except Exception as e:
        print(f"Error copying .inf file: {e}")
        return False

def modify_inf_line(file_path, line_number, new_value):
    """
    Modify a specific line in a PRESTO .inf file by line number
    
    Args:
        file_path: Path to the .inf file
        line_number: The line number to modify (1-based indexing)
        new_value: The new value to set after the equals sign
        
    Returns:
        bool: True if modification was successful, False otherwise
    """
    try:
        # Read the file content
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        # Check if the line number is valid
        if line_number < 1 or line_number > len(lines):
            print(f"Invalid line number {line_number}. File has {len(lines)} lines.")
            return False
            
        # Adjust for 0-based indexing
        line_index = line_number - 1
        
        # Check if the line contains an equals sign
        if '=' in lines[line_index]:
            # Split the line at the equals sign
            parts = lines[line_index].split('=')
            if len(parts) == 2:
                # Preserve the original formatting - keep the text before =
                lines[line_index] = f"{parts[0]}=  {new_value}\n"
            elif len(parts) > 2: 
                # Join all parts except the last one with '=' between them
                prefix = '='.join(parts[:-1])
                lines[line_index] = f"{prefix}=  {new_value}\n"
            else:
                print(f"Line {line_number} does not have the expected format.")
                return False
        else:
            print(f"Line {line_number} does not contain an equals sign.")
            return False
            
        # Write the modified content back to the file
        with open(file_path, 'w') as file:
            file.writelines(lines)
            
        # print(f"Successfully updated line {line_number} to have value '{new_value}' in {file_path}")
        return True
        
    except Exception as e:
        print(f"Error modifying .inf file: {e}")
        return False

def update_inf(file_dir, filename, bin_time, t0, pts, brks, target, ra, dec, analyzed_by, bary):
   
    copy_inf_file(args.template, file_dir, new_name=filename)
    
    inf_path = os.path.join(file_dir, filename + '.inf')
    
    #Lines
    ## 1 - filename
    modify_inf_line(inf_path, 1, filename)
    
    ## 4 - target
    modify_inf_line(inf_path, 4, target)
    
    ## 5 - RA
    modify_inf_line(inf_path, 5, ra)
    
    ## 6 - DEC
    modify_inf_line(inf_path, 6, dec)
    
    ## 8 - t0
    modify_inf_line(inf_path, 8, t0)
    
    ## 9 - Barycenter (0, 1)
    modify_inf_line(inf_path, 9, bary)
    
    ## 10 - N bins
    modify_inf_line(inf_path, 10, pts)
    
    ## 11 - bin_time
    modify_inf_line(inf_path, 11, bin_time)
    
    ## 12 - Breakss in data (0, 1)
    if brks:
        modify_inf_line(inf_path, 12, 1)
    else:
        modify_inf_line(inf_path, 12, 0)
    
    ## 18 - Analyzed by
    modify_inf_line(inf_path, 18, analyzed_by)
        
    return 0

radec_dict = {
    "crab": {"ra": "05:34:31.947", "dec": "22:00:52.15"},
    "geminga": {"ra": "06:33:54.153", "dec": "17:46:12.91"},
    "vela": {"ra": "08:35:20.655", "dec": "-45:10:35.15"},
    "psrj1227": {"ra": "12:27:58.748", "dec": "-48:53:42.82"},
    "psrj1023": {"ra": "10:23:47.684", "dec": "00:38:41.01"},
    "psrj0540": {"ra": "05:40:11.2", "dec": "-69:19:54.20"},
    "psrj1823": {"ra": "18:23:40.484", "dec": "-30:21:39.92"},
    "psrj1231": {"ra": "12:31:11.307", "dec": "-14:11:43.63"}
}

def main(args):

    if not args.name:
        args.name = "Astrolab"

    #file managing and setup
    temp_dir = pathlib.Path('/tmp')
    temp_folder = temp_dir / "fits2dat_temp"
    temp_folder.mkdir(parents=True, exist_ok=True)

    # input file
    fits_file = pathlib.Path(args.input_file)
    
    # Define filename
    filename = str(fits_file).split('_')[1].split('-')[0] + '_' + str(fits_file).split('_')[2].split('/')[0]

    # pulsar name
    # Try to get pulsar name from path or argument
    if args.pulsar_name:
        pulsar_name = args.pulsar_name
    else:
        pulsar_name = str(fits_file).split('/')[-3]
        if pulsar_name.lower() not in radec_dict:
            print(f"\nError: Pulsar name '{pulsar_name}' not found in dictionary. Please provide --pulsar_name.")
            sys.exit(1)

    # temp folder
    pulsar_temp_folder = temp_folder / pulsar_name
    pulsar_temp_folder.mkdir(parents=True, exist_ok=True)
    file_dir = str(temp_folder) + '/' + pulsar_name 
    file_path = str(temp_folder) + '/' + pulsar_name + '/' + filename
    
    # output dirs
    final_dir = str(args.output_dir)
    final_path = final_dir + '/' + filename #+ '_bary'

    #checking ra and dec
    if args.ra and args.dec:
        ra = args.ra
        dec = args.dec
    else:
        if pulsar_name.lower() not in radec_dict:
            print(f"\nError: Pulsar name '{pulsar_name}' not found in RA/DEC dictionary, please provide -ra and -dec.")
            sys.exit(1)
        ra = radec_dict[pulsar_name.lower()]['ra']
        dec = radec_dict[pulsar_name.lower()]['dec']
        
    print(f"Processing .fits file for {pulsar_name}")
    
    #read .fits
    a = fitsio.FITS(fits_file, "r")
    h1 = a[1].read_header()
    
    # get TOAs
    print('\r    Extracting time events...                         ', end='')
    if "TRJDREF" not in h1:
        MJDs = a[1].read_column("TIME") + float(h1["TMJDREF"])
    else:
        MJDs = a[1].read_column("TIME") + float(h1["TRJDREF"]) - 0.5
    
    os.makedirs(final_dir, exist_ok=True)
    
    # Status message
    print('\r    Writing events file...                           ', end='')
    MJDs.tofile(file_path + ".events")
    
    t0 = MJDs[0]
    pts = int((MJDs[-1] - MJDs[0]) * 86400 / float(args.bin_time)) + 1
    
    if h1['BARIC'] == 'NO':
        bary = 0
    else:
        bary = 1

    # Status message
    print('\r    Creating and updating .inf file...               ', end='')
    update_inf(file_dir, filename, args.bin_time, t0, pts, False, pulsar_name, ra, dec, args.name, bary)
    
    # Status message
    print('\r    Converting to .dat file...                       ', end='')
    cmd(f'toas2dat -n {pts} -t0 {t0} -dt {args.bin_time} -o {file_path}.dat {file_path}.events')
    
    if not args.no_bary:
        if h1['BARIC'] == 'NO':
            print('\r    Barycentering .dat file...                       ', end='')
            cmd(f'prepdata -o {final_path + '_bary'} {file_path}.dat')
        else:
            print('\r    Data already barycentered... skipping                       ', end='')
            cmd(f'prepdata -o {final_path + '_bary'} -nobary {file_path}.dat')
    else:
        print('\r    No barycentering requested... skipping                       ', end='')
        cmd(f'prepdata -o {final_path} -nobary {file_path}.dat')

    print('\r    Done                                             ')
    print()
    
    #cleaning pulsar folder
    try:
        shutil.rmtree(pulsar_temp_folder)
        print(f"Successfully removed temporary directory: {pulsar_temp_folder}")
    except Exception as e:
        print(f"Error while removing temporary directory: {e}")
        
    # Clean up the temporary directory
    print("Cleaning up temporary files...")
    try:
        shutil.rmtree(temp_folder)
        print(f"Successfully removed temporary directory: {temp_folder}")
    except Exception as e:
        print(f"Error while removing temporary directory: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=" Converts IQUEYE FITS files to PRESTO .dat format, optionally barycentering the data.\nThe script extracts time events from the FITS file, writes an events file, creates and updates a PRESTO .inf file, and generates a .dat file. \nIf barycentering is not disabled and the FITS file is not already barycentered, it will barycenter the .dat file using PRESTO's prepdata.")
    parser.add_argument('-t', '--template', required=True, help='Path to the template .inf file')
    parser.add_argument('-o', '--output_dir', required=True, help='Output directory for barycentered data')
    parser.add_argument('-dt', '--bin_time', required=True, help='Bin time wanted for the pulsar')
    parser.add_argument('-ra', '--ra', required=False, help='Right Ascension (RA) of the pulsar ex: 12:31:11.307')
    parser.add_argument('-dec', '--dec', required=False, help='Declination (DEC) of the pulsar ex: -45:10:35.15')
    parser.add_argument('-nobary', '--no_bary', action='store_true', help='Do not barycenter the data')
    parser.add_argument('--pulsar_name', required=False, help='Pulsar name (e.g., crab, geminga, vela)')
    parser.add_argument('--name', required=False, help='Name to use in PRESTO logs. Default value is "Astrolab"')
    parser.add_argument('input_file', help='Path to input .fits file')
    
    args = parser.parse_args()
    
    main(args)