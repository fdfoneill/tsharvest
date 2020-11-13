import geopandas, os, rasterio, shutil, subprocess
from pyproj import CRS

from .const import TEMP_DIR


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


def matchProjections(raster_path, shapefile_path, temp_dir = TEMP_DIR) -> tuple:
	"""Returns two file paths with matching projections

	Reprojects vector to match projection of raster (if
	necessary)

	Parameters
	----------
	raster_path:str
	vector_path:str

	Returns
	-------
	Tuple of out paths, one of which may be a new temporary
	file. The two files returned match in projection.
	"""
	# get raster projection as wkt
	with rasterio.open(raster_path,'r') as img:
		raster_wkt = img.profile['crs'].to_wkt()
	# get shapefile projection as wkt
	with open(shapefile_path.replace(".shp",".prj")) as rf:
		shapefile_wkt = rf.read()

	# if it's a match, nothing needs to be done
	if raster_wkt == shapefile_wkt:
		return (raster_path, shapefile_path)

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


	return(raster_path,out_shapefile_path)