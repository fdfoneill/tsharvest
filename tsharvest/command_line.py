# set up logging
import logging, os
from datetime import datetime, timedelta
logging.basicConfig(level=os.environ.get("LOGLEVEL","INFO"))
log = logging.getLogger(__name__)

import argparse, glob
from datetime import datetime
from .zonal import zonal_stats
from .util import *
from .const import *
from .exceptions import *


def multi_zonal_stats(input_vector:str, product:str, mask:str = None, start_date:str=None, end_date:str=None, full_archive:bool = False, verbose:bool = False, *args, **kwargs) -> dict:
	"""Run zonal.zonal_stats over multiple files

	***

	Parameters
	----------
	input_vector: str
		Path to vector zone file on disk
	product: str
		Name of desired product
	mask: str
		Name of desired crop mask
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
	verbose: bool
		Whether to log progress; default False
	args, kwargs
		Other arguments to be passed to
		zonal.zonal_stats

	"""
	startTime = datetime.now()

	if verbose:
		log.info("Starting multi_zonal_stats")

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
	if "merra-2" in product:
		data_directory = os.path.join(PRODUCT_DIR, "merra-2")
		merra_variable = product.split("-")[2]
		all_files = glob.glob(os.path.join(data_directory, f"merra-2.*.{merra_variable}.tif"))
		product = "merra-2"
	else:
		all_files = glob.glob(os.path.join(data_directory, f"{product}.*.tif"))

	# make sure some files were found
	assert len(all_files) > 0

	# filter by date
	data_dict = {}
	for f in all_files:
		file_date = dateFromFilePath(f)
		if start_date and (start_date > file_date):
			continue
		if end_date and (end_date < file_date):
			continue
		data_dict[file_date.strftime("%Y-%m-%d")] = f

	# make sure there's at least one file in the time period of interest
	assert len(data_dict) > 0

	# get crop mask
	if mask is not None:
		mask = os.path.join(MASK_DIR, f"{product}.{mask}.tif")
		assert os.path.exists(mask)

	if verbose:
		log.info("Burning shapefile to raster")
		burnTime = datetime.now()

	# define new file names
	reprojected_shape = os.path.join(TEMP_DIR,os.path.basename(input_vector))
	rasterized_shape = reprojected_shape.replace(os.path.splitext(reprojected_shape)[1],".tif")

	# reproject and rasterize shape
	model_raster = list(data_dict.values())[0]
	reproject_shapefile(input_vector, model_raster, reprojected_shape)
	shapefile_toRaster(reprojected_shape, model_raster, rasterized_shape)

	# make sure the rasterization worked
	assert os.path.exists(rasterized_shape)

	# cloud-optimize new raster
	cloud_optimize_inPlace(rasterized_shape)

	if verbose:
		log.info(f"Finished burning shapefile in {datetime.now() - burnTime}")
		log.info("Calculating zonal statistics")
		zoneTime = datetime.now()
	
	# meat and potatoes of processing
	full_output = {}
	for date in data_dict:
		if verbose:
			log.info(date)
		full_output[date] = zonal_stats(rasterized_shape, data_dict[date], mask, *args, **kwargs)

	# log time if necessary
	if verbose:
		log.info(f"Finished calculating in {datetime.now() - zoneTime}")
		log.info(f"Completed in {datetime.now() - startTime}")

	# return data
	return full_output


def stats_to_csv(stats_dictionary, output_csv) -> None:
	"""Writes statistics dictionary to csv format"""
	lines = []
	header = "date,zone,mean,pixels\n"
	lines.append(header)
	# generate lines
	for date in stats_dictionary:
		for zone in stats_dictionary[date]:
			line = f"{date},{zone},{stats_dictionary[date][zone]['value']},{stats_dictionary[date][zone]['pixels']}\n"
			lines.append(line)
	# write to file
	with open(output_csv,'w') as wf:
		wf.writelines(lines)


def main():
	parser = argparse.ArgumentParser(description="Calculate zonal statistics over a portion of the GLAM data archive")
	parser.add_argument("zone_shapefile",
		help="Path to zone shapefile")
	parser.add_argument("product_name",
		choices=[
			"MOD09Q1",
			"MYD09Q1",
			"MOD13Q1",
			"MYD13Q1",
			"chirps",
			"merra-2-min",
			"merra-2-mean",
			"merra-2-max",
			"swi"
			],
		help="Name of data product to be analyzed")
	parser.add_argument("out_path",
		help="Path to output csv file")
	parser.add_argument("-sd",
		"--start_date",
		help="Start of temporal range of interest, formatted as 'YYYY-MM-DD' or 'YYYY.DOY'")
	parser.add_argument("-ed",
		"--end_date",
		help="End of temporal range of interest, formatted as 'YYYY-MM-DD' or 'YYYY.DOY'")
	parser.add_argument("-f",
		"--full_archive",
		action="store_true",
		help="Must be set if neither start_date nor end_date are specified")
	parser.add_argument("-c",
		"--cores",
		default=20,
		required = True,
		help="Number of cores to use for parallel processing")
	parser.add_argument("-m",
		"--crop_mask",
		default = None,
		choices=[
			"maize",
			"rice",
			"soybean",
			"winterwheat",
			"springwheat",
			"cropland"
			],
		help="Name of crop mask to apply")
	parser.add_argument("-zf",
		"--zone_field",
		default=None,
		help="If shapefile has multiple zones, name of numeric field to use for zone values")
	parser.add_argument("-q",
		"--quiet",
		action="store_false",
		help="Suppress logging of progress and time")
	args = parser.parse_args()

	data = multi_zonal_stats(input_vector=args.zone_shapefile, product=args.product_name, mask=args.crop_mask, start_date=args.start_date, end_date=args.end_date, full_archive=args.full_archive, verbose=args.quiet, n_cores = args.cores)


	if not args.quiet:
		log.info("Writing data to csv")
	stats_to_csv(data,args.out_path)

	try:
		clean()
	except:
		log.warning("Failed to clear temp directory")

	log.info(f"Done. Output is at {args.out_path}")