#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 16:22:06 2023

IceSat2 download script

@author: jmaze
"""

# %% 1. Libraries and paths
# ----------------------------------------------------------------------------

import icepyx as ipx
import geopandas as gpd

download_path = '/Users/jmaze/Documents/projects/IceSat2-Lakes/data_raw/'

# %% 2. Download the IceSat2 data

# %%% 2.1 Import the study bounds

# Have to modify the supported drivers for GeoPandas to read ('r') .kml files
gpd.io.file.fiona.drvsupport.supported_drivers['LIBKML'] = 'r'

# Study bounds came from going to Google Earth and drawing an arbitrary box
bound_box = gpd.read_file(download_path + 'study_bounds.kml')

# Pulls the geometry from the first row of the dataframe using the iloc[] method
bound_box_geom = bound_box['geometry'].iloc[0]
# Remove the z dimension or icepyx.Query will spaz
coords_list = [(x, y) for x, y, z in bound_box_geom.exterior.coords]

del(bound_box_geom, bound_box)

# %%% 2.2 Specify the timeframe

# Timeframe for download, will dates outside the range make the icepyx spaz
begining = '2018-11-01'
end = '2023-12-01'
time = [begining, end]

# %%% 2.3 Create a ipx.Query object

# Pick spatial and temporal attributes
ATL06ds_identifier = ipx.Query(product = 'ATL06', 
                               spatial_extent = coords_list,
                               date_range = time)

# %%% 2.4 Download

# !!! When getting the granuales, 
# !!! You will need to enter Earth Data username and password here 
ATL06ds_identifier.order_granules()

# Download the data into folder. 
ATL06ds_identifier.download_granules(path = download_path + 'ATL06/')

