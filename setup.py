#!/usr/bin/env python

import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

def readme():
	with open('README.md') as f:
		return f.read()

exec(open('tsharvest/_version.py').read())

setup(name='tsharvest',
		version=__version__,
		description='Time series tool for NASA Harvest cluster',
		long_description=readme(),
		long_description_content_type='text/markdown',
		url="https://github.com/fdfoneill/tsharvest",
		author="F. Dan O'Neill",
		author_email='fdfoneill@gmail.com',
		license='MIT',
		packages=['tsharvest'],
		include_package_data=True,
		# third-party dependencies
		install_requires=[
			'geopandas',
			'pyshp',
			'pyproj',
			'gdal'
			],
		# classifiers
		classifiers=[
			"License :: OSI Approved :: MIT License",
			"Programming Language :: Python :: 3",
			"Programming Language :: Python :: 3.7",
			],
		# tests
		test_suite='nose.collector',
		tests_require=[
			'nose',
			'numpy'
			],
		zip_safe=False,
		# console scripts
		entry_points = {
			'console_scripts': [],
			}
		)