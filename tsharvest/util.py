# set up logging
import logging, os
from datetime import datetime, timedelta
logging.basicConfig(level=os.environ.get("LOGLEVEL","INFO"))
log = logging.getLogger(__name__)

import glob, os, rasterio, shutil, subprocess
import geopandas as gpd
from pyproj import CRS
from rasterio import features

from .const import *


# housekeeping utilities

def clean() ->  bool:
	"""Removes all files from TEMP_DIR"""
	allTemp = glob.glob(os.path.join(TEMP_DIR,"*"))
	for f in allTemp:
		try:
			os.remove(f)
		except Exception as e:
			log.warning(f"Failed to remove {os.path.basename(f)} from {TEMP_DIR}")


# raster/vector utilities

def cloud_optimize_inPlace(in_file:str,compress="LZW") -> None:
	"""Takes path to input and output file location. Reads tif at input location and writes cloud-optimized geotiff of same data to output location."""
	## add overviews to file
	cloudOpArgs = ["gdaladdo",in_file]
	subprocess.call(cloudOpArgs)

	## copy file
	intermediate_file = in_file.replace(".tif",".TEMP.tif")
	with open(intermediate_file,'wb') as a:
		with open(in_file,'rb') as b:
			shutil.copyfileobj(b,a)

	## add tiling to file
	cloudOpArgs = ["gdal_translate",intermediate_file,in_file,'-q','-co', "TILED=YES",'-co',"COPY_SRC_OVERVIEWS=YES",'-co', f"COMPRESS={compress}", "-co", "PREDICTOR=2"]
	subprocess.call(cloudOpArgs)

	## remove intermediate
	os.remove(intermediate_file)


def project_shapefile(shapefile_path, model_raster, out_path) -> tuple:
	"""Returns two file paths with matching projections

	Reprojects vector to match projection of raster (if
	necessary)

	Parameters
	---------_
	shapefile_path:str
		Path to shapefile that will be reprojected
	model_raster:str
		Path to model raster from which projection
		information will be extracted
	out_path: str
		Location on disk where output is to be
		written

	Returns
	-------
	String path to new reprojected shapefile
	"""
	# get raster projection as wkt
	with rasterio.open(model_raster,'r') as img:
		raster_wkt = img.profile['crs'].to_wkt()
	# get shapefile projection as wkt
	with open(shapefile_path.replace(".shp",".prj")) as rf:
		shapefile_wkt = rf.read()

	# if it's a match, nothing needs to be done
	if raster_wkt == shapefile_wkt:
		log.warning("CRS already match")
		# get input directory and filename
		in_dir = os.path.dirname(shapefile_path)
		in_name = os.path.splitext(os.path.basename(shapefile_path))[0]
		# list all elements of shapefile
		all_shape_files = glob.glob(os.path.join(in_dir,f"{in_name}.*"))
		# get output directory and filenames
		out_dir = os.path.dirname(out_path)
		out_name = os.path.splitext(os.path.basename(out_path))[0]
		for f in all_shape_files:
			name, ext = os.path.splitext(os.path.basename(f))
			out_f = os.path.join(out_dir,f"{out_name}{ext}")
			with open(f,'rb') as rf:
				with open(out_f,'wb') as wf:
					shutil.copyfileobj(rf,wf)
	else:
		# get CRS objects
		raster_crs = CRS.from_wkt(raster_wkt)
		shapefile_crs = CRS.from_wkt(shapefile_wkt)
		#transformer = Transformer.from_crs(raster_crs,shapefile_crs)

		# convert geometry and crs
		out_shapefile_path = out_path # os.path.join(temp_dir,os.path.basename(shapefile_path))
		data = gpd.read_file(shapefile_path)
		data_proj = data.copy()
		data_proj['geometry'] = data_proj['geometry'].to_crs(raster_crs)
		data_proj.crs = raster_crs

		# save output
		data_proj.to_file(out_shapefile_path)


	return out_shapefile_path


def shapefile_toRaster(shapefile_path, model_raster, out_path, zone_field:str = None) -> str:
	"""Burns shapefile into raster image
	
	***

	Parameters
	----------
	shapefile_path: str
		Path to input shapefile
	model_raster: str
		Path to existing raster dataset. Used for extent,
		pixel size, and other metadata. Output raster
		will be a pixel-for-pixel match of this
		dataset
	out_path: str
		Location where output rsater will be written on
		disk
	zone_field: str
		Field in shapefile to use as raster value. If None,
		flagged pixels will be written as "1" and non-flagged
		pixels will be written as NoData. Default None
	"""
	shp = gpd.read_file(shapefile_path)
	with rasterio.open(model_raster,'r') as rst:
		meta = rst.meta.copy()
	#meta.update(compress='packbits')

	with rasterio.open(out_path, 'w+', **meta) as out:
		out_arr = out.read(1)

		# this is where we create a generator of geom, value pairs to use in rasterizing
		if zone_field is not None: 
			zone_vals = []
			for i in range(len(shp)):
				zone_vals.append(shp.at[i,zone_field])
			shapes = ((geom,val) for geom, val in zip(shp.geometry,zone_vals))
		else:
			shapes = ((geom,1) for geom in shp.geometry)

		burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
		out.write_band(1, burned)

	return out_path


# processing utilities

def getWindows(width, height, blocksize) -> list:
	hnum, vnum = width, height
	windows = []
	for hstart in range(0, hnum, blocksize):
		for vstart in range(0, vnum, blocksize):
			hwin = blocksize
			vwin = blocksize
			if ((hstart + blocksize) > hnum):
				hwin = (hnum % blocksize)
			if ((vstart + blocksize) > vnum):
				vwin = (vnum % blocksize)
			targetwindow = Window(hstart, vstart, hwin, vwin)
			windows += [targetwindow]
	return windows

