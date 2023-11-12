#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 08:56:33 2023

@author: jmaze
"""

# %% 1. Libraries and directories
# ----------------------------------------------------------------------------
# ============================================================================

import geopandas as gpd
import pandas as pd
import fiona
import shapely
import pprint

# !!! Change this line for different local machines
working_dir = '/Users/jtmaz/Documents/projects/IceSat2-Lakes'
data_raw = working_dir + '/data_raw/'
data_intermediate = working_dir + '/data_intermediate/'

# %% 2. Greenland Lakes data and filter based on bouding box
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 2.1 Import the Lakes
gr_lakes = gpd.read_file(data_raw + 'Greenland_IIML_2017.shp')

# Lakes were imported with out a crs need to assign one.
print(gr_lakes.crs is None)

# Assinging manually from documentation WGS_1984_UTM_Zone_24N 
crs_proj = 'EPSG:32624' 

gr_lakes = gr_lakes.set_crs(crs = crs_proj)

# %%% 2.2 Import the project boundary

# Have to modify the supported drivers for GeoPandas to read ('r') .kml files
# !!! Read this line for MacOS
# gpd.io.file.fiona.drvsupport.supported_drivers['LIBKML'] = 'r'
# !!! read this line for Windows
fiona.drvsupport.supported_drivers['LIBKML'] = 'r'

# Study bounds came from going to Google Earth and drawing an arbitrary box
bound_box = gpd.read_file(data_raw + 'study_bounds.kml')
print(bound_box.crs)


# Bound box was imported with EPSG:4326, need to reassign
bound_box = bound_box['geometry'].to_crs(crs = crs_proj)
bound_box_geom = bound_box['geometry']
print(bound_box.crs)

# %%% 2.3 Filter the lakes dataset based on the project boundary

# Using using the geopandas.clip(), documentation is incorrect online
gr_lakes_filtered = gpd.clip(gr_lakes, bound_box)

# Clean up variable explorer
del(gr_lakes, bound_box)

# %% 3. Import the IceSat2 data and make it a geopandas object
# ----------------------------------------------------------------------------
# ============================================================================

icesat = pd.read_csv(data_intermediate + 'IceSat2_DataFrame.csv')

geometry = [shapely.Point(lon, lat) for lon, lat in zip(icesat['lon'], icesat['lat'])]

import geopandas as gpd

icesat_points = gpd.GeoDataFrame(icesat, geometry = geometry)

icesat_points = icesat_points.set_crs(crs = 'EPSG:4326')

icesat_points = icesat_points.to_crs(crs = 'EPSG:32624')

                
# %% 3. Import the IceSat2 data
# ----------------------------------------------------------------------------
# ============================================================================
         
icesat_filtered = gpd.clip(icesat_points, gr_lakes)

















