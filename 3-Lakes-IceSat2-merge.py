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

# Define CRS for project 
crs_proj = 'EPSG:32624'

# %% 2. Import Lakes data and filter based IceSat2 bouding box
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 2.1 Import the Lakes
LakesIIML = gpd.read_file(data_raw + 'IIML_raw_lakes2017.shp')

LakesGSWO = gpd.read_file(data_raw + 'GSWO_raw_lakes.shp')

# %%%% 2.1.1 Reformat GSWE Lakes

# Assinging CRS from documentation and reproject
crs_LakesGSWO = 'EPSG:4326'
LakesGSWO = LakesGSWO.set_crs(crs = crs_LakesGSWO)
LakesGSWO = LakesGSWO.to_crs(crs = crs_proj)
                             
# Make a new area column old one was in decimal degrees
LakesGSWO['area_m2'] = LakesGSWO.geometry.area

# Make a id column from ranking lake area
LakesGSWO['area_rank_id'] = LakesGSWO['area_m2'].rank(method = 'first', ascending = False).astype(int)
LakesGSWO['area_rank_id'] = 'ID_' + LakesGSWO['area_rank_id'].astype(str)

# Drop the original degrees area column
LakesGSWO = LakesGSWO.drop(columns = 'area')

# %%%% 2.1.2 Reformat the IIML lakes

# Designate the crs for LakesIIML
LakesIIML = LakesIIML.set_crs(crs = crs_proj)
LakesIIML = LakesIIML.drop(columns = ['LakeName', 'Source', 'NumOfSate', 'Certainty', 'Satellites'])
LakesIIML.rename(columns = {'Area':'area_m2', 'Length':'length_m', 'LakeID':'lake_id'}, inplace = True)

# %%% 2.2 Write the reformatted lake files to output
LakesGSWO.to_file(data_intermediate + 'LakesGSWO_v2.shp', index = False)
LakesIIML.to_file(data_intermediate + 'LakesIIML_v2.shp', index = False)

# %%% 2.3 Import the project boundary

# Have to modify the supported drivers for GeoPandas to read ('r') .kml files
# !!! Read this line for MacOS
# gpd.io.file.fiona.drvsupport.supported_drivers['LIBKML'] = 'r'
# !!! read this line for Windows
fiona.drvsupport.supported_drivers['LIBKML'] = 'r'

# Study bounds came from going to Google Earth and drawing an arbitrary box
bound_box = gpd.read_file(data_raw + 'study_bounds.kml')

# Bound box was imported with EPSG:4326, need to reassign
bound_box = bound_box.to_crs(crs = crs_proj)
bound_box = bound_box['geometry']

# %%% 2.4 Filter the lakes dataset based on the project boundary

# Using using the geopandas.clip(), documentation is incorrect online
LakesIIML = gpd.clip(LakesIIML, bound_box)
LakesGSWO = gpd.clip(LakesGSWO, bound_box)

# Check out the area distribution of different lake datasets
# IIML lakes
plt.hist(LakesIIML['area_m2'], bins = 50)
plt.show()

# GSWE lakes
plt.hist(LakesGSWO['area_m2'], bins = 50)
plt.show()

# %% 3. Import the IceSat2 data & make them gpd object
# ----------------------------------------------------------------------------
# ============================================================================

# Read the IceSat2 data
IceSat = pd.read_csv(data_intermediate + 'IceSat2_DataFrame_v1.csv')

# Convert the dataframes lat and long to a GDF with point geometry. 
geometry = [shapely.Point(lon, lat) for lon, lat in zip(IceSat['lon'], IceSat['lat'])]
IceSatPts = gpd.GeoDataFrame(IceSat, geometry = geometry)

# Reproject the icesat data to match the gr_lakes
IceSatPts = IceSatPts.set_crs(crs = 'EPSG:4326')
IceSatPts = IceSatPts.to_crs(crs = crs_proj)
     
        
# %% 4. Spatial join the IceSat2 data to the GR lakes
# ----------------------------------------------------------------------------
# ============================================================================
        
# Spatially join the IceSat points to the IMLL lakes
IceSatJoinedIIML = gpd.sjoin(IceSatPts, 
                             LakesIIML, # Elimnates Icesat points that don't fall within a lake. 
                             how = 'inner', # Eliminates IceSat points not matched with a Lake
                             op = 'within') # Icesat points need to be inside a lake

#Spatially join the IceSat points to the GSWO lakes
IceSatJoinedGSWO = gpd.sjoin(IceSatPts, 
                             LakesGSWO, 
                              how = 'inner',
                              op = 'within')

# Reformat the columns for IIML
IceSatJoinedIIML = IceSatJoinedIIML.drop(columns = ['index_right', 'Unnamed: 0', 'lat', 'lon'])

# Reformat the columns for GSWE
IceSatJoinedGSWO.drop(columns = ['Unnamed: 0', 'lat', 'lon', 'index_right'], inplace = True)

# %% 5. Write the files to intermediate folder
# ----------------------------------------------------------------------------
# ============================================================================

# Write the spatially joined file to output
IceSatJoinedIIML.to_file(data_intermediate + 'ICESat2_pts_IIML.shp', index = False) 
                                       
# Write the spatially joined file to output
IceSatJoinedGSWO.to_file(data_intermediate + 'ICESat2_pts_GSWO.shp', index = False) 















