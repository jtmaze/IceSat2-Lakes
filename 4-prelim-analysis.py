#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Nov 12 16:34:39 2023

@author: jmaze
"""

# %% 1. Libraries and directories
# ----------------------------------------------------------------------------
# ============================================================================

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# !!! Change this for different local machines
working_dir = '/Users/jtmaz/Documents/projects/IceSat2-Lakes'
data_output = working_dir + '/data_output/'

# %% 2. Read the data and explore basic attributes
# ----------------------------------------------------------------------------
# ============================================================================

lake_pts_icesat = gpd.read_file(data_output + 'lake_pts_icesat.shp')

# Need to make the LakeID a string
lake_pts_icesat['LakeID'] = lake_pts_icesat['LakeID'].astype(str)

# How many points are we looking at per lake?
(lake_pts_icesat['LakeID'].value_counts())

# Generate an interesting summary table for each lake
summary1 = lake_pts_icesat.groupby('LakeID').agg({'height': 'std',
                                                  'Area': 'first',
                                                  'LakeID': 'size'})

# Change the column names for the summary dataframe. 
summary1.columns = ['height_std', 'lake_area', 'observation_count']

# Filter lakes that don't have ridiculously high std?
summary1_robust = summary1.query('height_std < 50 & observation_count > 10')
# Relationship between observation count and height_std?
summary1_robust.plot.scatter(x = 'observation_count', y = 'height_std')
# Relationship between lake_area and height_std?
summary1_robust.plot.scatter(x = 'lake_area', y = 'height_std')

# %% 3. Plot the distributions of altimeter measurements for the different lakes
# ----------------------------------------------------------------------------
# ============================================================================

# Isolate the best lakes from orgininal data
robust_lake_pts = lake_pts_icesat[lake_pts_icesat['LakeID'].isin(summary1_robust.index)]
# Make an array of good lake IDs
robust_LakeIDs = robust_lake_pts['LakeID'].unique()

robust_lake_pts()

# Make the figure
fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 4
cols = 5

for i, lake_id in enumerate(robust_LakeIDs):
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    dataplot = robust_lake_pts[robust_lake_pts['LakeID'] == lake_id]
    # Generate a histogram
    plt.hist(dataplot['height'], bins = 42)
    # Plot title
    plt.title(f'Lake ID = {lake_id}')

plt.tight_layout()   
plt.show()
    
# %% 3. Plot the distributions of altimeter measurements for the different lakes
# ----------------------------------------------------------------------------
# ============================================================================   
    
    
    



