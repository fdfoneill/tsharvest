import os

TEMP_DIR = os.path.join(os.path.dirname(__file__),"temp")
if not os.path.exists(TEMP_DIR):
	os.path.mkdir(TEMP_DIR)

PRODUCT_DIR = r"/gpfs/data1/cmongp2/GLAM/rasters/products/"

TEST_SHP = r"/gpfs/data1/cmongp2/oneilld/2020-11_parallelized_zonal_stats/example_shapefile/Ann_township.shp"
TEST_TIF = r"/gpfs/data1/cmongp2/GLAM/rasters/products/MOD09Q1/MOD09Q1.2020.001.tif"

MASK_DIR = r"/gpfs/data1/cmongp2/GLAM/gdp/glam_data_processing/glam_data_processing/statscode/Masks"