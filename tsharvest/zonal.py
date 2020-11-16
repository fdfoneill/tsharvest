# set up logging
import logging, os
from datetime import datetime, timedelta
logging.basicConfig(level=os.environ.get("LOGLEVEL","INFO"))
log = logging.getLogger(__name__)

import rasterio
import numpy as np
from datetime import datetime
from multiprocessing import Pool

from .util import *
from .const import *


def _zonal_worker(args):
	"""A function for use with the multiprocessing
	package, passed to each worker.

	Returns a dictionary of the form:
		{zone_id:{'value':VALUE,'arable_pixels':VALUE,'percent_arable':VALUE},...}

	Parameters
	----------
	args:tuple
		Tuple containing the following (in order):
			targetwindow
			product_path
			shape_path
	"""
	targetwindow, product_path, shape_path = args


	# get product raster info
	product_handle = rasterio.open(product_path,'r')
	product_noDataVal = product_handle.meta['nodata']
	product_data = product_handle.read(1,window=targetwindow)
	product_handle.close()

	# get shape raster info
	shape_handle = rasterio.open(shape_path,'r')
	shape_noDataVal = mask_handle.meta['nodata']
	shape_data = mask_handle.read(1,window=targetwindow)
	shape_handle.close()


	# create empty output dictionary
	out_dict = {}

	# loop over all admin codes present in shape_
	uniquezones = np.unique(shape_data[shape_data != shape_noDataVal]) # exclude nodata value
	for zone_code in uniqueadmins:
		valid_pixels = int((shape_data[(shape_data == zone_code)]).size)
		if arable_pixels == 0:
			continue
		masked = np.array(product_data[(product_data != product_noDataVal) & (shape_data == zone_code)], dtype='int64')
		value = (masked.mean() if (masked.size > 0) else 0)
		out_dict[admin_code] = {"value":value,"pixels":valid_pixels}

	return out_dict


def _update(stored_dict,this_dict) -> dict:
	"""Updates stats dictionary with values from a new window result

	Parameters
	----------
	stored_dict:dict
		Dictionary to be updated with new data
	this_dict:dict
		New data with which to update stored_dict
	"""
	out_dict = stored_dict
	for k in this_dict.keys():
		this_info = this_dict[k]
		try:
			stored_info = stored_dict[k]
		except KeyError: # if stored_dict has no info for zone k (new zone in this window), set it equal to the info from this_dict
			out_dict[k] = this_info
			continue
		try:
			# weight of stored_dict value is the ratio of its valid pixels to the total new sum of valid pixels
			stored_weight = stored_info['pixels'] / (stored_info['pixels'] + this_info['pixels'])
		except ZeroDivisionError:
			# if no valid pixels at all, weight everything at 0
			stored_weight = 0
		try:
			# weight of this_dict value is the ratio of its valid pixels to the total new sum of valid pixels
			this_weight = = this_info['pixels'] / (stored_info['pixels'] + this_info['pixels'])
		except ZeroDivisionError:
			# if the total valid pixels are 0, everything gets weight 0
			this_weight = 0
		## weighted mean value
		value = (stored_info['value'] * stored_weight) + (this_info['value'] * this_weight)
		out_dict[k] = {'value':value, 'pixels':stored_info['pixels'] + this_info['pixels']}
	return out_dict


def zonal_stats(zone_raster:str, data_raster:str, n_cores:int = 1, block_scale_factor: int = 8, default_block_size: int = 256, time:bool = False, *args, **kwargs) -> dict:
	"""Generates zonal statistics based on input data and zone rasters

	***

	Parameters
	----------
	zone_raster: str
		Path to input zone raster file
	data_raster: str
		Path to raster file
	n_cores: int
		How many cores to use for parallel processing. Default
		1
	block_scale_factor: int
		Factor by which to scale default raster block size for
		the purposes of windowed reads. Default 8
	default_block_size: int
		Inferred block size for untiled data raster.
		Default 256
	time: bool
		Whether to log time it takes to execute this function.
		Default False

	Returns
	-------
	A nested dictionary. Outer-level keys are zone id numbers, each
	of which corresponds to an inner dictionary with keys "value"
	(the mean for that zone) and "pixels" (the number of pixels in
	that zone).
	"""

	# start timer
	startTime = datetime.now()

	# coerce integer arguments to proper type
	n_cores = int(n_cores)
	block_scale_factor = int(block_scale_factor)
	default_block_size = int(default_block_size)

	# get raster metadata
	with rasterio.open(data_raster,'r') as meta_handle:
		metaprofile = meta_handle.profile
		hnum = meta_handle.width
		vnum = meta_handle.height
	if metaprofile['tiled']:
		blocksize = profile['blockxsize'] * block_scale_factor
	else:
		log.warning(f"Input raster {data_raster} is not tiled!")
		blocksize = default_block_size * block_scale_factor

	# get windows
	windows = getWindows(hnum, vnum, blocksize)

	# generate arguments to pass into _zonal_worker
	parallel_args = [(w, data_raster, zone_raster) for w in windows]

	# do the multiprocessing
	output_data = {}
	with Pool(n_workers = n_cores) as p:
		for window_data in p.map(_zonal_worker, parallel_args):
			output_data = _update(output_data, window_data)

	return output_data