# set up logging
import logging, os
from datetime import datetime, timedelta
logging.basicConfig(level=os.environ.get("LOGLEVEL","INFO"))
log = logging.getLogger(__name__)

import fiona
from shapely.geometry import Point, shape
from .const import *


def indices_to_coords(x, y, geomatrix) -> tuple:
	"""Returns geographic coordinates of pixel

	Calculates coordinates at x,y based on 
	geomatrix

	***

	Parameters
	----------
	x:int
		Column position of pixel within image
	y:int
		Row position of pixel within image
	geomatrix:geomatrix
		As returned by gdal.GetGeoTransform()

	Returns
	-------
	Tuple of geographic coordinates in
	form (x, y). Note that output will be in
	the projected coordinates of input geomatrix
	"""

	ulX = geomatrix[0]
	ulY = geomatrix[3]
	xDist = geomatrix[1]
	yDist = geomatrix[5]
	rtnX = geomatrix[2]
	rtnY = geomatrix[4]

	geoX = ulX + (xDist * x)
	geoY = ulY + (yDist * y)

	return (geoX, geoY)


def coords_within_poly(x, y, shapefile_path) -> bool:
	"""Return whether the point at passed coordinates falls within a polygon shapefile

	***

	Parameters
	----------
	x: float
	y: float
	shapefile_path: str
		Path to a polygon shapefile; must be in the same
		projection as geo coordinates

	Returns
	-------
	True if point falls within shapefile; False otherwise
	"""
	point = Point(x,y)
	polygons = [pol for pol in fiona.open(shapefile_path)]
	for j, poly in enumerate(polygons):
		if not point.within(shape(poly['geometry'])):
			return False
	return True