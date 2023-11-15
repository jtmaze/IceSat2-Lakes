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
import datetime as dt

# !!! Change this for different local machines
working_dir = '/Users/jmaze/Documents/projects/IceSat2-Lakes'
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

# Per this documentation:
# https://nsidc.org/sites/default/files/icesat2_atl06_data_dict_v003_0.pdf
# delta_time is seconds since 2018-01-01


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

# %%% 2.3 Summarize IceSat data by lake

# Generate an interesting summary table for each lake
summary1 = lake_pts_icesat.groupby('LakeID').agg({'height': ['std', 'mean'],
                                                  'Area': 'first',
                                                  'LakeID': 'size',
                                                  'obs_date': [lambda x: x.unique().astype(str).tolist(), # Get a list of unique obs dates
                                                               lambda x: len(x.unique().astype(str).tolist())] # Counts each unique obs date
                                                  })
# Since there's a LakeID column, reset the index
summary1.reset_index(inplace = True)

# Make the column names more legible
summary1.columns = ['LakeID', 'lake_height_std', 'lake_height_mean', 'lake_area', 
                   'lake_observation_count','lake_obs_dates', 'unique_dates_count']


# %%% 2.4 Query for lakes w. robust data

# Filter lakes that don't have ridiculously high std?
summary1_robust = summary1.query('lake_height_std < 30 & lake_observation_count > 25')

# %%% 2.5 Visualize summary stats

# Relationship between observation count and height_std?
summary1.plot.scatter(x = 'lake_observation_count', y = 'lake_height_std')
summary1_robust.plot.scatter(x = 'lake_observation_count', y = 'lake_height_std')
# Relationship between lake_area and height_std?
summary1.plot.scatter(x = 'lake_area', y = 'lake_height_std')
summary1_robust.plot.scatter(x = 'lake_area', y = 'lake_height_std')
# Relationship between lake_area and total observation_count?
summary1.plot.scatter(x = 'lake_area', y = 'lake_observation_count')
summary1_robust.plot.scatter(x = 'lake_area', y = 'lake_observation_count')
# Relationship between lake_area and unique dates
summary1.plot.scatter(x = 'lake_area', y = 'unique_dates_count')
summary1_robust.plot.scatter(x = 'lake_area', y = 'unique_dates_count')

# %% 3. Plot the distributions of elevation by LakeID
# ----------------------------------------------------------------------------
# ============================================================================

# Isolate the best lakes from orgininal data
robust_lake_pts = lake_pts_icesat[lake_pts_icesat['LakeID'].isin(summary1_robust['LakeID'])]

# Join info from robust summary to the lake pts. 
robust_lake_pts = pd.merge(robust_lake_pts, 
                            summary1_robust, 
                            how = 'left', 
                            on = 'LakeID')

# Make new column for range from mean for each value
robust_lake_pts['diff_from_mean'] = (robust_lake_pts['height'] - robust_lake_pts['lake_height_mean'])

#!!! Filter lake pts based on the distance from the mean
robust_lake_pts = robust_lake_pts.query('-100 < diff_from_mean < 100')

# Subset the data by LakeID for plotting
subset_LakeIDs = summary1_robust['LakeID'].iloc[36:42]
subset_lake_pts = robust_lake_pts[robust_lake_pts['LakeID'].isin(subset_LakeIDs)]


# Make the figure
fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 3
cols = 2

for i, lake_id in enumerate(subset_LakeIDs):
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    dataplot = robust_lake_pts[robust_lake_pts['LakeID'] == lake_id]
    # Generate a histogram
    plt.hist(dataplot['diff_from_mean'], bins = 50)
    # Plot title
    plt.title(f'Lake ID = {lake_id}')

plt.tight_layout()
plt.show()

# Clean up variable explorer

    
# %% 3. Plot the distributions of altimeter measurements for the different lakes
# ----------------------------------------------------------------------------
# ============================================================================   
    
    
    



