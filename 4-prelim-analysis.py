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
import geoplot as gplt

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
# Lakes were imported with out a crs need to assign one.
print(gr_lakes.crs is None)
# Assinging manually from documentation WGS_1984_UTM_Zone_24N 
crs_proj = 'EPSG:32624' 
# Define crs for the Greenland Lakes
gr_lakes = gr_lakes.set_crs(crs = crs_proj)

# Read the filtered IceSat2 points. 
lake_pts_icesat = gpd.read_file(data_output + 'lake_pts_icesat.shp')

# Need to make the LakeID a string
lake_pts_icesat['LakeID'] = lake_pts_icesat['LakeID'].astype(str)

# How many points are we looking at per lake?
(lake_pts_icesat['LakeID'].value_counts())

# %%% 2.2 Convert delta_time to a legible date

# Per this documentation:
# https://nsidc.org/sites/default/files/icesat2_atl06_data_dict_v003_0.pdf
# delta_time is the number of seconds since 2018-01-01


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

# %%% 2.3 Make a column to designate lake phase

def lake_phaser (obs_date):
    # !!! Check with Johnny on this approximate designation
    szn_dict = {'frozen': [11, 12, 1, 2, 3, 4], # Nov thru April are frozen?
                'intermediate_spring': [5], 
                'intermediate_fall': [10], # May and Oct are intermediate?
                'liquid': [6, 7, 8, 9]} # June, July, August and September are liquid?
    
    month = obs_date.month # Extract the month from the datetime object. 
    
    # Designate lake_phase_est based on szn_dict
    if month in szn_dict['frozen']:
        lake_phase_est = 'frozen'
    if month in szn_dict['intermediate_spring']:
        lake_phase_est = 'intermediate_spring'
    if month in szn_dict['intermediate_fall']:
        lake_phase_est = 'intermediate_fall'
    if month in szn_dict['liquid']:
        lake_phase_est = 'liquid'

    return(lake_phase_est)

# Run the function on the dataframe
lake_pts_icesat = lake_pts_icesat.assign(lake_phase_est = lake_pts_icesat['obs_date'].apply(lake_phaser))

# %%% 2.4 Summarize IceSat data by lake

# Generate an interesting summary table for each lake
summary1 = lake_pts_icesat.groupby('LakeID').agg({'height': ['std', 'mean'],
                                                  'Area': 'first',
                                                  'LakeID': 'size',
                                                  'obs_date': [lambda x: x.unique().astype(str).tolist(), # Get a list of unique obs dates
                                                               lambda x: len(x.unique().astype(str).tolist())] # Counts each unique obs date
                                                  })
# Reset the index to make LakeID a simple column
summary1.reset_index(inplace = True)

# Make the column names more legible
summary1.columns = ['LakeID', 'lake_height_std', 'lake_height_mean', 'lake_area', 
                   'lake_observation_count','lake_obs_dates', 'unique_dates_count']


# %%% 2.5 Query for lakes w. robust data

# Query lakes that don't have ridiculously large height stdv
# Also get lakes with a sizeable observation count
summary1_robust = summary1.query('lake_height_std < 30 & lake_observation_count > 15')

# %%% 2.6 Visualize summary stats for 'robust' and original datasets

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

# %%% 3.1 Subset and reformat the data for plotting

# Isolate the best lakes from orgininal IceSat data
robust_lake_pts = lake_pts_icesat[lake_pts_icesat['LakeID'].isin(summary1_robust['LakeID'])]

# Join info from robust summary table to the Icesat lake pts. 
robust_lake_pts = pd.merge(robust_lake_pts, 
                            summary1_robust, 
                            how = 'left', 
                            on = 'LakeID')

# Make new column for difference from mean for each value
robust_lake_pts['diff_from_mean'] = (robust_lake_pts['height'] - robust_lake_pts['lake_height_mean'])
#!!! Filter lake pts based on the distance from the mean
robust_lake_pts = robust_lake_pts.query('-100 < diff_from_mean < 100')

# Subset the data by LakeID for plotting
# Choose the LakeIDs with lowest standard deviation for height. 
subset_LakeIDs = summary1_robust.sort_values('lake_height_std').iloc[0:20]
# Create a series with the lowest standard dev of lake IDs
subset_LakeIDs_series = pd.Series(subset_LakeIDs['LakeID'])
# Subset the lake points for plotting
subset_lake_pts = robust_lake_pts[robust_lake_pts['LakeID'].isin(subset_LakeIDs_series)]

# Clean up variables
# del(summary1, summary1_robust, lake_pts_icesat)

# %%% 3.2 Make the figure
fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 4
cols = 5
colors_dict = {'frozen': 'grey', 'intermediate_spring': 'green', 
               'liquid': 'blue', 'intermediate_fall': 'red'}

for i, lake_id in enumerate(subset_LakeIDs_series):
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    dataplot = subset_lake_pts[subset_lake_pts['LakeID'] == lake_id]
    # Get lake phases for each LakeID
    lake_phases = dataplot['lake_phase_est'].unique()
    # Itereate through lake phases and plot color bars
    for lake_phase in lake_phases:
        phase_data = dataplot[dataplot['lake_phase_est'] == lake_phase]['diff_from_mean']
        # Generate a histogram
        plt.hist(phase_data, bins = 25, 
                 color = colors_dict.get(lake_phase, 'grey'))
                 # Plot title
    plt.title(f'Lake ID = {lake_id}')
    

plt.tight_layout()
plt.show()

del(i, lake_id, lake_phase, lake_phases, phase_data, 
    rows, cols, colors_dict, dataplot, fig)
    
# %% 4. Make maps of some lakes. 
# ----------------------------------------------------------------------------
# ============================================================================   

# Not sure how geoplot is better than matplotlib?
map_ID = '3250'
shape = gr_lakes.query('LakeID == 3250')
points = robust_lake_pts.query('LakeID == 3250')


ax = gplt.polyplot(shape)
gplt.pointplot(points, ax=ax)
    
gplt.show()



