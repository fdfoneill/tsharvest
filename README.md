# tsharvest

A Python package for easy time-series analysis of NASA Harvest GLAM system data

![NASA Harvest logo](https://nasaharvest.org/sites/default/files/harvestlogo18_1.png)

# Motivation

The GLAM system (glam.nasaharvest.org) is a web-based, visualization and analysis tool that utilizes near-real time MODIS and VIIRS land surface reflectance products in tandem with a variety of other datasets to empower continuous crop condition monitoring. One result of the GLAM workflow is that large amounts of earth observation data are stored in Cloud-Optimized Geotiff (COG) format on the NASA Harvest computing cluster. This trove of data is an ideal subject for time-series analysis, allowing (with the right tools) for the quick and easy extraction of environmental indicators over a long temporal period.

This `tsharvest` package aims to fill the role of those 'right tools' for time-series analysis. It offers a simple command-line interface through which NASA Harvest users can provide their own regions of interest in vector format, specify their desired temporal period, and output zonal statistics in comma-separated value (CSV) format. 

# Features

* Leverages the GEOG High-Performance Computing (HPC) cluster, taking advantage of parallel workflows to greatly improve processing speed
* Accepts user-provided vector region files, optionally stratified by zone
* Produces output in CSV format
* Can be subset temporally with start and end dates for analysis

# How to Use

## Synopsis

```
tsharvest

[-h] [-sd START_DATE] [-ed END_DATE] [-f] -c CORES
[-zf ZONE_FIELD] [-q]
zone_shapefile
{MOD09Q1,MYD09Q1,MOD13Q1,MYD13Q1,chirps,merra-2-min,merra-2-mean,merra-2-max,swi}
out_path
```

## Description

The `tsharvest` console script can be used to calculate zonal statistics over a portion of the GLAM data archive.

* `-h, --help`

	* Show help message and exit.

* `-sd START_DATE, --start_date <START_DATE>`

	* Start of temporal range of interest, formatted as 'YYYY-MM-DD' or 'YYYY.DOY'

* `-ed END_DATE, --end_date <END_DATE>`

	* End of temporal range of interest, formatted as 'YYYY-MM-DD' or 'YYYY.DOY'

* `-f, --full_archive`

	* This flag must be set if neither start_date nor end_date are specified.

* `-c CORES, --cores <CORES>`

	* Number of cores to use for parallel processing. Recommended default is 20; remember to check current usage!

* `-zf ZONE_FIELD, --zone_field <ZONE_FIELD>`

	* If shapefile has multiple zones, name of numeric field to use for zone values.

* `-q, --quiet`

	* Suppress logging of progress and time.

* `<zone_shapefile>`

	* Path to polygon shapefile that demarcates zones / region of interest.
 
* `<{MOD09Q1,MYD09Q1,MOD13Q1,MYD13Q1,chirps,merra-2-min,merra-2-mean,merra-2-max,swi}>`

	* Name of data product to be analyzed.
 
* `<out_path>`

	* Path to output csv file.

## Examples

`tsharvest polygon.shp "MOD09Q1" time_series_output.csv -sd "2019-01-01" -ed "2020-01-01" -c 20`

To output CHIRPS rainfall zonal statistics for each "ADM1_CODE" zone, for the full CHIRPS archive:

`tsharvest gaul1.shp "chirps" zonal_rainfall_output.csv -zf "ADM1_CODE" -f -c 20`

To calculate the maximum temperature in a zone from 2017 to the present:

`tsharvest polygon.shp "merra-2-max" temperature_max.csv -sd "2019.001" -c 20`

# License

MIT License

Copyright (c) 2020 F. Dan O'Neill

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.