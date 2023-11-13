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
import matplotlib.pyplot as plt


# !!! Change this line for different local machines
working_dir = '/Users/jmaze/Documents/projects/IceSat2-Lakes'

# Subfolders
data_raw = working_dir + '/data_raw/'
data_intermediate = working_dir + '/data_intermediate/'
data_output = working_dir + '/data_output/'

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
bound_box = gpd.read_file(data_raw + 'study_bounds_small.kml')
print(bound_box.crs)


# Bound box was imported with EPSG:4326, need to reassign
bound_box = bound_box.to_crs(crs = crs_proj)
bound_box_geom = bound_box['geometry']
print(bound_box.crs)

# %%% 2.3 Filter the lakes dataset based on the project boundary

# Using using the geopandas.clip(), documentation is incorrect online
gr_lakes_filtered = gpd.clip(gr_lakes, bound_box)

# Get rid of the extra large lakes
# gr_lakes_filtered = gr_lakes_filtered.query('Area < 200000')

# Clean up variable explorer
# del(gr_lakes, bound_box)

# Check out the area distribution of different lakes
plt.hist(gr_lakes_filtered['Area'], bins = 50)
plt.yscale('log')
plt.show()

# Query again based on the area distribution
# gr_lakes_filtered = gr_lakes_filtered.query('75000 < Area < 150000')

# %% 3. Import the IceSat2 data and make it a geopandas object
# ----------------------------------------------------------------------------
# ============================================================================

# Read the IceSat2 data
icesat = pd.read_csv(data_intermediate + 'IceSat2_DataFrame.csv')

# Convert the dataframes lat and long to a GDF with point geometry. 
geometry = [shapely.Point(lon, lat) for lon, lat in zip(icesat['lon'], icesat['lat'])]
icesat_points = gpd.GeoDataFrame(icesat, geometry = geometry)

# Reproject the icesat data to match the gr_lakes
icesat_points = icesat_points.set_crs(crs = 'EPSG:4326')
icesat_points = icesat_points.to_crs(crs = crs_proj)

                
# %% 4. Spatial join the IceSat2 data to the GR lakes
# ----------------------------------------------------------------------------
# ============================================================================
        
# Spatially join the 
icesat_filtered = gpd.sjoin(icesat_points, 
                            gr_lakes_filtered, # Elimnates Icesat points that don't fall within a lake. 
                            how = 'inner', # Eliminates IceSat points not matched with a Lake
                            op = 'within') # Icesat points need to be inside a lake

# Drop useless cols
icesat_filtered = icesat_filtered.drop(columns = ['index_right', 'Unnamed: 0', 'lat', 'lon'])
# There's some unreasonable huge values for height
icesat_filtered = icesat_filtered.query('height < 10000')

# Write the spatially joined file to output
icesat_filtered.to_file(data_output + 'lake_pts_icesat.shp',
                        index = False) # Not sure why I need to set this to Fales
                                       # code won't work unless I do. 

















