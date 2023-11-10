#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 08:56:33 2023

@author: jmaze
"""

# %% 1. Libraries
# ----------------------------------------------------------------------------
# ============================================================================

import icepyx as ipx
import geopandas as gpd

data_path = '/Users/jmaze/Documents/projects/IceSat2-Lakes/data_raw/'

# %% 2. Greenland Lakes data and filter based on bouding box
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 2.1 Import the Lakes
gr_lakes = gpd.read_file(data_path + 'Greenland_IIML_2017.shp')

# Lakes were imported with out a crs need to assign one.
print(gr_lakes.crs is None)

# Assinging manually from documentation WGS_1984_UTM_Zone_24N 
crs_proj = 'EPSG:32624' 

gr_lakes = gr_lakes.set_crs(crs = crs_proj)

# %%% 2.2 Import the project boundary

# Have to modify the supported drivers for GeoPandas to read ('r') .kml files
gpd.io.file.fiona.drvsupport.supported_drivers['LIBKML'] = 'r'

# Study bounds came from going to Google Earth and drawing an arbitrary box
bound_box = gpd.read_file(data_path + 'study_bounds.kml')
print(bound_box.crs)

# Bound box was imported with EPSG:4326, need to reassign
bound_box = bound_box.to_crs(crs = crs_proj)
bound_box = bound_box['geometry']
print(bound_box.crs)

# %%% 2.3 Filter the lakes dataset based on the project boundary

# Using using the geopandas.clip(), documentation is incorrect online
gr_lakes_filtered = gpd.clip(gr_lakes, bound_box)

# %% 3. Import the IceSat2 data
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 3.1 File patterns for icepyx

ATL06_path = data_path + 'ATLO6/'

# Since data was downloaded directly from NSIDC it has the following convention 
# "ATL{product:2}_{datetime:%Y%m%d%H%M%S}_{rgt:4}{cycle:2}{orbitsegment:2}_{version:3}_{revision:2}.h5"

pattern = pattern = "processed_ATL{product:2}_{datetime:%Y%m%d%H%M%S}_{rgt:4}{cycle:2}{orbitsegment:2}_{version:3}_{revision:2}.h5"

# %%% 3.1 File patterns for icepyx