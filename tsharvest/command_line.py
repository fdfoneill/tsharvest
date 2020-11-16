# set up logging
import logging, os
from datetime import datetime, timedelta
logging.basicConfig(level=os.environ.get("LOGLEVEL","INFO"))
log = logging.getLogger(__name__)

import argparse, glob
from .zonal import zonal_stats
from .const import *
from .exceptions import *


def multi_zonal_stats(input_vector:str, product:str, start_date:str, end_date:str, full_archive:bool = False, *args, **kwargs) -> dict:
	"""Run zonal.zonal_stats over multiple files

	***

	Parameters
	----------
	input_vector: str
		Path to vector zone file on disk
	product: str
	start_date: str
		Beginning date of imagery to be analyzed,
		inclusive. Format as either
			"YYYY-MM-DD" or
			"YYYY.DOY"
	end_date: str

	full_archive: bool
		If start_date and end_date are not
		set, this flag must be set to True
		in order to process a full product
		archive. Default False
	args, kwargs
		Other arguments to be passed to
		zonal.zonal_stats

	"""
	# validate arguments
	if start_date:
		start_date = parseDateString(start_date)
	if end_date:
		end_date = parseDateString(end_date)
	if (not start_date) and (not end_date):
		if not full_archive:
			raise BadInputError("If full_archive is False, must set either start_date or end_date!")

	# get list of data files to be analyzed
	data_directory = os.path.join(PRODUCT_DIR, product)
	assert os.path.exists(data_directory) # make sure they didn't mistype the product
	all_files = glob.glob(os.path.join(data_directory, "*.tif"))
	data_dict = {}
	for f in all_files:
		try:
			file_date = parseDateString(".".join(os.path.basename(f).split(".")[1:4]))
		except IndexError:
			file_date = parseDateString(os.path.basename(f).split(".")[1])
		if start_date and (start_date > file_date):
			continue
		if end_date and (end_date < file_date):
			continue
		data_dict[file_date.strftime("%Y-%m-%d")] = f

	# make sure there's at least one file in the time period of interest
	assert len(data_dict) >= 1

	# define new file names
	reprojected_shape = os.path.join(TEMP_DIR,os.path.basename(input_vector))
	rasterized_shape = reprojected_shape.replace(os.path.splitext(reprojected_shape)[1],".tif")

	# reproject and rasterize shape
	model_raster = list(data_dict.values())[0]
	reproject_shapefile(input_vector, model_raster, reprojected_shape)
	shapefile_toRaster(reprojected_shape, model_raster, rasterized_shape)

	# make sure the rasterization worked
	assert os.path.exists(rasterized_shape)
	
	# meat and potatoes of processing
	full_output = {}
	for date in data_dict:
		full_output[date] = zonal_stats(rasterized_shape, data_dict[date], *args, **kwargs)

	return full_output
