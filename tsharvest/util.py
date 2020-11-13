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


def clean() ->  bool:
	"""Removes all files from TEMP_DIR"""
	allTemp = glob.glob(os.path.join(TEMP_DIR,"*"))
	for f in allTemp:
		try:
			os.remove(f)
		except Exception as e:
			log.warning(f"Failed to remove {os.path.basename(f)} from {TEMP_DIR}")


def cloud_optimize_inPlace(in_file:str) -> None:
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
	cloudOpArgs = ["gdal_translate",intermediate_file,in_file,'-q','-co', "TILED=YES",'-co',"COPY_SRC_OVERVIEWS=YES",'-co', "COMPRESS=LZW", "-co", "PREDICTOR=2"]
	subprocess.call(cloudOpArgs)

	## remove intermediate
	os.remove(intermediate_file)


def matchProjection(shapefile_path, raster_path, temp_dir = TEMP_DIR) -> tuple:
	"""Returns two file paths with matching projections

	Reprojects vector to match projection of raster (if
	necessary)

	Parameters
	---------_
	shapefile_path:str
		Path to shapefile that will be reprojected
	raster_path:str
		Path to model raster from which projection
		information will be extracted


	Returns
	-------
	String path to new reprojected shapefile
	"""
	# get raster projection as wkt
	with rasterio.open(raster_path,'r') as img:
		raster_wkt = img.profile['crs'].to_wkt()
	# get shapefile projection as wkt
	with open(shapefile_path.replace(".shp",".prj")) as rf:
		shapefile_wkt = rf.read()

	# if it's a match, nothing needs to be done
	if raster_wkt == shapefile_wkt:
		log.warning("CRS already match. Returning input path.")
		return shapefile_path

	# get CRS objects
	raster_crs = CRS.from_wkt(raster_wkt)
	shapefile_crs = CRS.from_wkt(shapefile_wkt)
	#transformer = Transformer.from_crs(raster_crs,shapefile_crs)

	# convert geometry and crs
	out_shapefile_path = os.path.join(temp_dir,os.path.basename(shapefile_path))
	data = gpd.read_file(shapefile_path)
	data_proj = data.copy()
	data_proj['geometry'] = data_proj['geometry'].to_crs(raster_crs)
	data_proj.crs = raster_crs

	# save output
	data_proj.to_file(out_shapefile_path)


	return out_shapefile_path


def shapefile_toRaster(shapefile_path, raster_path, out_path) -> str:
	shp = gpd.read_file(shapefile_path)
	with rasterio.open(raster_path,'r') as rst:
		meta = rst.meta.copy()

	with rasterio.open(out_path, 'w+', **meta) as out:
		out_arr = out.read(1)

		# this is where we create a generator of geom, value pairs to use in rasterizing
		shapes = ((geom,1) for geom in shp.geometry)

		burned = features.rasterize(shapes=shapes, fill=0, out=out_arr, transform=out.transform)
		out.write_band(1, burned)

	return out_path