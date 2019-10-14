
import os
import gdal
import numpy as np
import xarray as xr
from rasterio import logging as rio_logging
import subprocess
from datetime import datetime as dt

def get_times(vrt_fname):
    """
    Extract time info from file metadata
    """
    d = gdal.Open(vrt_fname)
    fnames = d.GetFileList()
    # First file name is the VRT file name
    fnames = fnames[1::]

    # Empty times list
    times = []
    for fname in fnames:
        d = gdal.Open(fname)
        # Get metadata
        md = d.GetMetadata()

        # Get fields with date info
        start_date = md['RANGEBEGINNINGDATE']
        times.append(np.datetime64(start_date))

    return times

def get_times_from_file_band(fname):
    """
    Extract time info from band metadata
    """
    d = gdal.Open(fname)
    bands = d.RasterCount

    # Empty times list
    times = []

    for band in range(bands):
        b = d.GetRasterBand(band+1)
        # Get band metadata
        md = b.GetMetadata()

        # Get fields with date info
        start_date = md['RANGEBEGINNINGDATE']
        times.append(np.datetime64(start_date))

    return times

def generate_output_fname(output_dir, fname):
    """
    Generate an output file name
    """
    postfix = os.path.basename(output_dir)

    fname = os.path.basename(fname)
    fname = os.path.splitext(fname)[0]
    fname = os.path.join(output_dir,
                         f"{fname}.{postfix}.tif")

    return fname

def run_command(cmd: str):
    """
    Executes a command in the OS shell
    :param cmd: command to execute
    :return:
    """
    status = subprocess.call([cmd], shell=True)

    if status != 0:
        err_msg = f"{cmd} \n Failed"
        raise Exception(err_msg)

def string_to_date(str_date: str):
    """
    Converts a string in three possible layouts into a dt object
    :param str_date: String in three different formats:
                     2002-05-28 '%Y-%m-%d'
                     January 1, 2001 '+%B%e, %Y'
                     Present
    :return _date: datetime object
    """
    # Remove upper cases and spaces
    str_date = str_date.lower().replace(' ', '')
    if str_date.lower() == 'present':
        _date = dt.now()
        return _date

    try:
        # Try default format YYYY-mm-dd
        _date = dt.strptime(str_date, '%Y-%m-%d')
    except ValueError as e:
        try:
            # Try alternative format, e.g. January 1, 2001
            _date = dt.strptime(str_date, '+%B%e, %Y' )
        except ValueError:
            raise(e)

    return _date

def get_chunk_size(filename):
    """
    Extract the block size and raster count so that the
    chunks tuple can be formed, a parameter needed to read
    a dataset using xr.open_rasterio() using DASK.
    :param filename: GDAL valid file.
    :return: tuple raster count, x block size, y block size
    """

    # Extract raster count and block size from file
    d = gdal.Open(filename)
    raster_count = d.RasterCount
    # Get internal block size from first band
    b = d.GetRasterBand(1)
    block_size = b.GetBlockSize()
    chunks = (raster_count, block_size[0], block_size[1])

    return chunks
