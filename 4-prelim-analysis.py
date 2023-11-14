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
# import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt

# !!! Change this for different local machines
working_dir = '/Users/jtmaz/Documents/projects/IceSat2-Lakes'
data_output = working_dir + '/data_output/'
data_raw = working_dir + '/data_raw/'

# %% 2. Read the IceSat2 data & explore basic attributes
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 2.1 Read the lake boundaries and IceSat2 points.

# Read the lake boundaries?
gr_lakes = gpd.read_file(data_raw + 'Greenland_IIML_2017.shp')

# Read the filtered IceSat2 points. 
lake_pts_icesat = gpd.read_file(data_output + 'lake_pts_icesat.shp')

# Need to make the LakeID a string
lake_pts_icesat['LakeID'] = lake_pts_icesat['LakeID'].astype(str)

# How many points are we looking at per lake?
(lake_pts_icesat['LakeID'].value_counts())

# %%% 2.2 Convert delta_time to a legible date

# Writing a function and using the .apply method should make this faster for large data. 
def calendar_from_delta (delta_time):
    # Make a datetime objct based on the ATL06 epoch
    ATL06_epoch = dt.datetime(2018, 1, 1)
    # Make time delta_time a datetime object (seconds)
    delta_time_seconds = dt.timedelta(seconds = delta_time)
    # Add the seconds since the ATL06 epoch to the epoch. 
    obs_date = delta_time_seconds + ATL06_epoch
    # Truncate time information for just ymd
    obs_date = obs_date.date()
    
    return(obs_date)

# Run the function on the DataFrame. 
lake_pts_icesat = lake_pts_icesat.assign(obs_date = lake_pts_icesat['delta_time'].apply(calendar_from_delta))

#Checking on the function
lake_pts_icesat = lake_pts_icesat.sort_values('obs_date')

# %%% 2.2 Summarize IceSat data by lake

# Generate an interesting summary table for each lake
summary1 = lake_pts_icesat.groupby('LakeID').agg({'height': ['std', 'mean'],
                                                  'Area': 'first',
                                                  'LakeID': 'size',
                                                  'obs_date': ['unique']
                                                  })

# Change the column names for the summary dataframe. 
summary1.columns = ['lake_height_std', 'lake_height_mean', 'lake_area', 
                    'lake_observation_count', 'lake_obs_dates']


# %%% 2.3 Query for lakes w. robust data

# Filter lakes that don't have ridiculously high std?
summary1_robust = summary1.query('height_std < 30 & observation_count > 25')

# %%% 2.3 Visualize 

# Relationship between observation count and height_std?
summary1_robust.plot.scatter(x = 'lake_observation_count', y = 'lake_height_std')
# Relationship between lake_area and height_std?
summary1_robust.plot.scatter(x = 'lake_area', y = 'lake_height_std')
# Relationship between lake_area and observation_count?
summary1_robust.plot.scatter(x = 'lake_area', y = 'lake_observation_count')

# %% 3. Plot the distributions of elevation by LakeID
# ----------------------------------------------------------------------------
# ============================================================================

# Slice a handfull of rows (LakeIDs) to make plotting more manageable. 
# summary1_robust_sample = summary1_robust.iloc[0:20]

# Isolate the best lakes from orgininal data
robust_lake_pts = lake_pts_icesat[lake_pts_icesat['LakeID'].isin(summary1_robust.index)]

# Join info from robust summary to the lake pts. 
t = 

# Make new column for range from mean for each value
robust_lake_pts['diff_mean_height'] = robust_lake_pts['height']

# Make an array of good lake IDs
robust_LakeIDs = robust_lake_pts['LakeID'].unique()

# Make the figure
fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 3
cols = 4

for i, lake_id in enumerate(robust_LakeIDs):
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    dataplot = robust_lake_pts[robust_lake_pts['LakeID'] == lake_id]
    # Generate a histogram
    plt.hist(dataplot['height'], bins = 50)
    # Plot title
    plt.title(f'Lake ID = {lake_id}')

plt.tight_layout()
plt.show()
    
# %% 3. Plot the distributions of altimeter measurements for the different lakes
# ----------------------------------------------------------------------------
# ============================================================================   
    
    
    



