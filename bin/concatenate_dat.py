#!/usr/bin/env python
"""
Concatenate PRESTO .dat Files

This script concatenates multiple PRESTO .dat files into a single time series,
handling gaps between observations by filling them with the mean value and
ensuring the output has a highly factorable number of points for efficient FFTs.

Author: Pascual Marcone
Version: 1.0.0
Date: 14th August 2025
"""

__version__ = "1.0.0"
__author__ = "Pascual Marcone"
__email__ = "pascual.marcone@ug.uchile.cl"

import os
import numpy as np
from typing import List, Tuple, Dict, Any, Union
import sys
import argparse
import time
import matplotlib.pyplot as plt

def choose_good_N(orig_N: int) -> int:
    """
    Choose a time series length that is larger than the input value but
    that is highly factorable for efficient FFT computation.
    
    This function finds the smallest number >= orig_N that is either:
    1. A highly factorable number from a predefined list, or
    2. A power of 2
    
    The function prioritizes numbers that factor well into small primes,
    which leads to more efficient FFT algorithms.
    
    Parameters
    ----------
    orig_N : int
        Original number of points in the time series
        
    Returns
    -------
    int
        A highly factorable number >= orig_N, optimized for FFT performance
        
    Examples
    --------
    >>> choose_good_N(1500)
    1536
    >>> choose_good_N(2000)
    2000
    >>> choose_good_N(10000)
    10000
    """
    goodfactors = [1000, 1008, 1024, 1056, 1120, 1152, 1200, 1232,
                   1280, 1296, 1344, 1408, 1440, 1536, 1568, 1584,
                   1600, 1680, 1728, 1760, 1792, 1920, 1936, 2000,
                   2016, 2048, 2112, 2160, 2240, 2304, 2352, 2400,
                   2464, 2560, 2592, 2640, 2688, 2800, 2816, 2880,
                   3024, 3072, 3136, 3168, 3200, 3360, 3456, 3520,
                   3584, 3600, 3696, 3840, 3872, 3888, 3920, 4000,
                   4032, 4096, 4224, 4320, 4400, 4480, 4608, 4704,
                   4752, 4800, 4928, 5040, 5120, 5184, 5280, 5376,
                   5488, 5600, 5632, 5760, 5808, 6000, 6048, 6144,
                   6160, 6272, 6336, 6400, 6480, 6720, 6912, 7040,
                   7056, 7168, 7200, 7392, 7680, 7744, 7776, 7840,
                   7920, 8000, 8064, 8192, 8400, 8448, 8624, 8640,
                   8800, 8960, 9072, 9216, 9408, 9504, 9600, 9680,
                   9856, 10000]
    
    if orig_N <= 0:
        return 0
        
    def is_power_of_10(n: int) -> bool:
        """
        Check if n is a power of 10.
        
        Parameters
        ----------
        n : int
            Number to check
            
        Returns
        -------
        bool
            True if n is a power of 10, False otherwise
        """
        if n <= 0:
            return False
        while n > 1:
            if n % 10 != 0:
                return False
            n //= 10
        return True
    
    # Get the number represented by the first 4 digits of orig_N
    first4_str = str(orig_N)[:4]
    first4 = int(first4_str)
    
    # Find the appropriate good factor
    small_N = None
    for factor in goodfactors:
        # Check to see if orig_N is a goodfactor times a power of 10
        if factor == first4 and orig_N % factor == 0 and is_power_of_10(orig_N // factor):
            small_N = factor
            break
        if factor > first4:
            small_N = factor
            break
    
    # If no factor found, use the largest one
    if small_N is None:
        small_N = goodfactors[-1]
    
    # Scale up small_N until it's >= orig_N
    while small_N < orig_N:
        small_N *= 10
    
    # Find the closest power of 2 greater than orig_N
    two_N = 2
    while two_N < orig_N:
        two_N *= 2
    
    # Return the smaller of the two options
    if two_N < small_N:
        return two_N
    else:
        return small_N

def read_inf(file: str) -> Dict[str, str]:
    """
    Read PRESTO .inf file and parse its contents into a dictionary.
    
    PRESTO .inf files contain metadata about time series observations,
    including observation parameters, telescope information, and data
    file specifications.
    
    Parameters
    ----------
    file : str
        Path to the .inf file
        
    Returns
    -------
    Dict[str, str]
        Dictionary containing key-value pairs from the .inf file
        
    Raises
    ------
    FileNotFoundError
        If the .inf file doesn't exist
    IOError
        If there's an error reading the file
        
    Examples
    --------
    >>> inf_data = read_inf("observation.inf")
    >>> print(inf_data['Epoch of observation (MJD)'])
    58000.123456
    """
    inf_data = {}
    
    with open(file, 'r') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('Any additional notes:'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                inf_data[key] = value
            elif line.startswith('Any additional notes:'):
                # Handle the notes section which may span multiple lines
                notes = []
                for note_line in f:
                    note_line = note_line.strip()
                    if note_line:
                        notes.append(note_line)
                inf_data['Any additional notes'] = '\n'.join(notes)
                break
    
    return inf_data

def read_dat(file: str) -> Tuple[np.ndarray, int, Dict[str, str]]:
    """
    Read PRESTO .dat file and its corresponding .inf file.
    
    This function safely reads binary time series data from a .dat file
    using a temporary backup to avoid corruption, and also reads the
    associated metadata from the .inf file.
    
    Parameters
    ----------
    file : str
        Path to the .dat file (without extension)
        
    Returns
    -------
    Tuple[np.ndarray, int, Dict[str, str]]
        - data: Time series data as float32 numpy array
        - N: Number of data points
        - inf_data: Dictionary containing .inf file metadata
        
    Raises
    ------
    FileNotFoundError
        If .dat or .inf files don't exist
    IOError
        If there's an error reading the files
        
    Examples
    --------
    >>> data, N, inf = read_dat("observation.dat")
    >>> print(f"Loaded {N} data points")
    >>> print(f"Time resolution: {inf['Width of each time series bin (sec)']} seconds")
    """
    backup_file = file + ".bak"
    inffile = os.path.splitext(file)[0] + ".inf"
    
    # Safely read .dat data using backup file to prevent corruption
    os.rename(file, backup_file)
    time.sleep(0.002)  # Small delay to ensure file system sync
    data = np.fromfile(backup_file, dtype=np.float32)
    N = len(data)
    os.rename(backup_file, file)
    
    # Read corresponding inf file
    inf_data = read_inf(inffile)
    
    return data, N, inf_data

def write_dat(data: np.ndarray, output_file: str, base_inf_data: Dict[str, str], init_mjd: float) -> None:
    """
    Write concatenated data to .dat file and create corresponding .inf file.
    
    This function writes the time series data in binary format and creates
    an updated .inf file with proper metadata for the concatenated dataset.
    
    Parameters
    ----------
    data : np.ndarray
        Time series data to write (will be cast to float32)
    output_file : str
        Output filename without extension
    base_inf_data : Dict[str, str]
        .inf file metadata from first input file to use as template
    init_mjd : float
        Initial MJD (Modified Julian Date) for the concatenated time series
        
    Raises
    ------
    IOError
        If there's an error writing the files
        
    Examples
    --------
    >>> write_dat(concatenated_data, "output", inf_template, 58000.0)
    # Creates output.dat and output.inf
    """
    dat_file = output_file + '.dat'
    inf_file = output_file + '.inf'
    
    # Write binary data in PRESTO format (float32)
    data.astype(np.float32).tofile(dat_file)
    
    # Create updated inf file with new metadata
    updated_inf = base_inf_data.copy()
    updated_inf['Data file name without suffix'] = os.path.basename(output_file)
    updated_inf['Epoch of observation (MJD)'] = str(init_mjd)
    updated_inf['Number of bins in the time series'] = str(len(data))
    
    # Write inf file with proper formatting
    with open(inf_file, 'w') as f:
        for key, value in updated_inf.items():
            if key == 'Any additional notes':
                f.write(f"Any additional notes:\n")
                f.write(f"Concatenated using concatenate_dat.py v{__version__}\n")
                f.write(f"Original notes: {value}\n" if value else "")
            else:
                f.write(f" {key} = {value}\n")

def concatenate_dats(files: List[str]) -> Tuple[float, np.ndarray, Dict[str, str]]:
    """
    Concatenate multiple PRESTO .dat files into a single time series.
    
    This function handles the main concatenation logic:
    1. Reads all input files and sorts them chronologically
    2. Validates consistency of time bin widths
    3. Fills gaps between observations with mean values
    4. Ensures final array has a highly factorable length for FFT efficiency
    
    Parameters
    ----------
    files : List[str]
        List of paths to .dat files to concatenate
        
    Returns
    -------
    Tuple[float, np.ndarray, Dict[str, str]]
        - init_mjd: Starting MJD of concatenated time series
        - final_data: Concatenated time series data
        - inf_data: .inf metadata from first chronological file
        
    Raises
    ------
    ValueError
        If time bin widths are inconsistent or files overlap in time
    FileNotFoundError
        If any input files are missing
        
    Examples
    --------
    >>> files = ["obs1.dat", "obs2.dat", "obs3.dat"]
    >>> mjd, data, inf = concatenate_dats(files)
    >>> print(f"Concatenated {len(files)} files into {len(data)} points")
    """
    # Initialize arrays for storing file data
    data = np.empty(len(files), dtype=object)
    Ns = np.zeros(len(files), dtype=int)
    infs = np.empty(len(files), dtype=object)
    
    # Read all input files
    print("Reading input files...")
    for i, file in enumerate(files):
        print(f"  Reading {file}")
        data[i], Ns[i], infs[i] = read_dat(file)
    
    # Validate time bin width consistency
    dt_values = [float(inf['Width of each time series bin (sec)']) for inf in infs]
    if not len(set(dt_values)) == 1:
        raise ValueError(f"Time series bin widths are not consistent: {dt_values}")
    else:
        dt = dt_values[0]
        print(f"Time resolution: {dt} seconds")
    
    # Sort files by observation epoch (chronological order)
    epochs = [float(inf['Epoch of observation (MJD)']) for inf in infs]
    sorted_indices = np.argsort(epochs)
    
    # Reorder arrays according to sorted epochs
    data = data[sorted_indices]
    Ns = Ns[sorted_indices] 
    infs = infs[sorted_indices]
    epochs = np.array(epochs)[sorted_indices]
    
    print(f"Files sorted chronologically from MJD {epochs[0]:.6f} to {epochs[-1]:.6f}")
    
    # Calculate overall mean for gap filling
    all_values = np.concatenate(data)
    observation_mean = np.mean(all_values)
    print(f"Using mean value {observation_mean:.6f} for gap filling")
    
    # Start with first dataset
    final_data = data[0].copy()
    
    # Process each subsequent file
    for i in range(len(infs) - 1):
        init_mjd = epochs[i]
        next_init = epochs[i+1]
        
        # Filter out non-finite values (if any)
        valid_mask = np.isfinite(data[i])
        data[i] = data[i][valid_mask]
        Ns[i] = len(data[i])
        
        # Calculate end time of current observation
        end_mjd = init_mjd + (Ns[i] * dt) / 86400.0  # Convert seconds to days
        
        # Check for temporal overlaps
        if end_mjd > next_init:
            overlap_hours = (end_mjd - next_init) * 24
            raise ValueError(f"Time series overlap at index {i}: {overlap_hours:.2f} hours")
        
        # Calculate gap duration and fill with mean values
        gap_duration_days = next_init - end_mjd
        gap_duration_seconds = gap_duration_days * 86400.0
        fill_points = int(gap_duration_seconds / dt)
        
        if fill_points > 0:
            print(f"  Filling {gap_duration_seconds/3600:.2f} hour gap with {fill_points} points")
            temp_fill = np.full(fill_points, observation_mean, dtype=np.float32)
            final_data = np.append(final_data, temp_fill)
        
        # Append next observation
        if i < len(data) - 1:
            final_data = np.append(final_data, data[i+1])
    
    # Calculate optimal final array size for FFT efficiency
    init_mjd = epochs[0]
    final_inf = infs[-1]
    end_mjd = epochs[-1] + float(final_inf['Number of bins in the time series']) * dt / 86400.0
    
    expected_points = int((end_mjd - init_mjd) * 86400.0 / dt)
    optimal_points = choose_good_N(expected_points)
    
    # Pad to optimal size if necessary
    if optimal_points > len(final_data):
        padding_points = optimal_points - len(final_data)
        print(f"Padding with {padding_points} points to reach optimal size {optimal_points}")
        final_fill = np.full(padding_points, observation_mean, dtype=np.float32)
        final_data = np.append(final_data, final_fill)

    print(f"Final time series: {len(final_data)} points, {len(final_data)*dt/3600:.2f} hours")
    return init_mjd, final_data, infs[0]
    
def main() -> None:
    """
    Main function to handle command-line interface and orchestrate concatenation.
    
    Parses command-line arguments, validates inputs, and performs the 
    concatenation of PRESTO .dat files.
    """
    parser = argparse.ArgumentParser(
        description=f'Concatenate PRESTO .dat files (v{__version__})',
        epilog="""
        This tool concatenates multiple PRESTO .dat time series files into a single
        file, handling temporal gaps by filling them with mean values and ensuring
        the output has an optimal length for FFT processing.
        
        Example:
            python concatenate_dat.py obs1.dat obs2.dat obs3.dat -o combined
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('files', nargs='+', 
                       help='Input .dat file paths to concatenate')
    parser.add_argument('-o', '--output', required=True,
                       help='Output file path (without extension)')
    parser.add_argument('--version', action='version', 
                       version=f'concatenate_dat.py {__version__}')
    
    args = parser.parse_args()
    
    # Validate input files exist
    for file in args.files:
        if not os.path.exists(file):
            print(f"Error: Input file {file} not found")
            sys.exit(1)
        inf_file = os.path.splitext(file)[0] + ".inf"
        if not os.path.exists(inf_file):
            print(f"Error: Corresponding .inf file {inf_file} not found")
            sys.exit(1)
    
    print(f"PRESTO .dat Concatenation Tool v{__version__}")
    print("=" * 50)
    print(f"Input files: {len(args.files)}")
    for i, file in enumerate(args.files, 1):
        print(f"  {i}. {file}")
    print(f"Output: {args.output}.dat")
    print()
    
    try:
        # Perform concatenation
        init_mjd, concatenated_data, inf_data = concatenate_dats(args.files)
        
        # Write output files
        print("Writing output files...")
        write_dat(concatenated_data, args.output, inf_data, init_mjd)
        
        print("=" * 50)
        print("Successfully concatenated all files!")
        print(f"Output files: {args.output}.dat, {args.output}.inf")
        
    except Exception as e:
        print(f"Error during concatenation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
