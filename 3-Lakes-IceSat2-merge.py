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
import matplotlib.pyplot as plt


# !!! Change this line for different local machines
working_dir = '/Users/jmaze/Documents/projects/IceSat2-Lakes'

# Subfolders
data_raw = working_dir + '/data_raw/'
data_intermediate = working_dir + '/data_intermediate/'
data_output = working_dir + '/data_output/'

# %% 2. Import Lakes data and filter based IceSat2 bouding box
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 2.1 Import the Lakes
gr_lakes_IIML = gpd.read_file(data_raw + 'Greenland_IIML_2017.shp')

gr_lakes_GSW = gpd.read_file(data_raw + 'gr_lakes_better.shp')

# Make a new column for lake_id based on area ranking.
gr_lakes_GSW['area_rank_id'] = gr_lakes_GSW['area'].rank(method = 'first', ascending = False).astype(int)
gr_lakes_GSW['area_rank_id'] = 'ID_' + gr_lakes_GSW['area_rank_id'].astype(str)

# Lakes were imported with out a crs need to assign one.
print(gr_lakes_IIML.crs is None)
print(gr_lakes_GSW.crs is None)

# Assinging manually from documentation WGS_1984_UTM_Zone_24N 
crs_proj = 'EPSG:32624' 
crs_lakes_GSW = 'EPSG:4326'

# Designate the CRS for the IIML lakes
gr_lakes_IIML = gr_lakes_IIML.set_crs(crs = crs_proj)

# Designate the orginal CRS for the better lakes data then reproject. 
gr_lakes_GSW = gr_lakes_GSW.set_crs(crs = crs_lakes_GSW)
gr_lakes_GSW = gr_lakes_GSW.to_crs(crs = crs_proj)

# Write the GSW dataframe with the area rank
gr_lakes_GSW.to_file(data_output + 'gr_lakes_GSW_v2.shp',
                     index = False)

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
bound_box = bound_box.to_crs(crs = crs_proj)
bound_box_geom = bound_box['geometry']
print(bound_box.crs)

# %%% 2.3 Filter the lakes dataset based on the project boundary

# Using using the geopandas.clip(), documentation is incorrect online
lakes_IIML_filtered = gpd.clip(gr_lakes_IIML, bound_box)
lakes_GSW_filtered = gpd.clip(gr_lakes_GSW, bound_box)

# Clean up variable explorer
del(gr_lakes_IIML, bound_box, gr_lakes_GSW)

# Check out the area distribution of different lake datasets

# IIML lakes
plt.hist(lakes_IIML_filtered['Area'], bins = 50)
plt.yscale('log')
plt.show()

# Better lakes
plt.hist(lakes_GSW_filtered['area'], bins = 50)
plt.yscale('log')
plt.show()

# %% 3. Import the IceSat2 data and make it a geopandas object
# ----------------------------------------------------------------------------
# ============================================================================

# Read the IceSat2 data
icesat = pd.read_csv(data_intermediate + 'IceSat2_DataFrame_v1.csv')

# Convert the dataframes lat and long to a GDF with point geometry. 
geometry = [shapely.Point(lon, lat) for lon, lat in zip(icesat['lon'], icesat['lat'])]
icesat_points = gpd.GeoDataFrame(icesat, geometry = geometry)

# Reproject the icesat data to match the gr_lakes
icesat_points = icesat_points.set_crs(crs = 'EPSG:4326')
icesat_points = icesat_points.to_crs(crs = crs_proj)

del(geometry, crs_proj, crs_lakes_GSW, bound_box_geom)        
        
# %% 4. Spatial join the IceSat2 data to the GR lakes
# ----------------------------------------------------------------------------
# ============================================================================
        
# Spatially join the IceSat points to the IMLL lakes
icesat_joined_IIML = gpd.sjoin(icesat_points, 
                               lakes_IIML_filtered, # Elimnates Icesat points that don't fall within a lake. 
                               how = 'inner', # Eliminates IceSat points not matched with a Lake
                               op = 'within') # Icesat points need to be inside a lake

#Spatially join the IceSat points to the better GSW lakes
icesat_joined_GSW = gpd.sjoin(icesat_points, 
                              lakes_GSW_filtered, 
                              how = 'inner',
                              op = 'within')

# Reformat the columns for IIML
icesat_joined_IIML = icesat_joined_IIML.drop(columns = ['index_right', 'Unnamed: 0', 'lat', 'lon'])

# Reformat the columns for GSW
icesat_joined_GSW = icesat_joined_GSW.rename(columns = {'index_right': 'LakeID', 'area': 'Area'})
icesat_joined_GSW.drop(columns = ['Unnamed: 0', 'lat', 'lon'], inplace = True)

# There's some unreasonably huge values for height
icesat_joined_IIML = icesat_joined_IIML.query('height < 10000')
icesat_joined_GSW = icesat_joined_GSW.query('height < 10000')

# Write the spatially joined file to output
icesat_joined_IIML.to_file(data_output + 'IIML_lake_pts_icesat.shp',
                        index = False) # Not sure why I need to set this to False
                                       # code won't work unless I do. 
                                       
# Write the spatially joined file to output
icesat_joined_GSW.to_file(data_output + 'GSW_lake_pts_icesat.shp',
                        index = False) # Not sure why I need to set this to False
                                       # code won't work unless I do.                                        

















