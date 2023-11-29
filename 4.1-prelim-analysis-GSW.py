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

# Read the lake boundaries
gsw_lakes = gpd.read_file(data_output + 'gr_lakes_GSW_v2.shp')
# Lakes were imported with out a crs need to assign one.
print(gsw_lakes.crs is None)

# Assinging manually from documentation WGS 1984 ellipsoidal

# crs_gsw = 'EPSG:4326'
# Define crs for the Greenland Lakes
# gsw_lakes = gsw_lakes.set_crs(crs = crs_gsw)

# Reproject the Greenland Lakes
#crs_proj = 'EPSG:32624'
#gsw_lakes = gsw_lakes.to_crs(crs = crs_proj)

# Read the filtered IceSat2 points. 
lake_pts = gpd.read_file(data_output + 'GSW_lake_pts_icesat.shp')

# Need to make the LakeID a string
lake_pts = lake_pts.drop(columns = ['LakeID'])
lake_pts = lake_pts.rename(columns = {'area_rank_': 'area_rank_id'})

# How many points are we looking at per lake?
(lake_pts['area_rank_id'].value_counts())

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
lake_pts = lake_pts.assign(obs_date = lake_pts['delta_time'].apply(calendar_from_delta))

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
lake_pts = lake_pts.assign(lake_phase_est = lake_pts['obs_date'].apply(lake_phaser))

# %%% 2.4 Summarize IceSat data by lake

# Generate an interesting summary table for each lake
summary1 = lake_pts.groupby('area_rank_id').agg({'height': ['std', 'mean'],
                                           'Area': 'first', # Take the first value for lake area
                                           'area_rank_id': 'size', # size function counts the number of observations
                                           'obs_date': [lambda x: x.unique().astype(str).tolist(), # Get a list of unique obs dates
                                                        lambda x: len(x.unique().astype(str).tolist())] # Counts each unique obs date
                                           })

# Reset the index to make LakeID a simple column
summary1.reset_index(inplace = True)

# Make the column names more legible
summary1.columns = ['area_rank_id', 'lake_height_std', 'lake_height_mean', 'lake_area', 
                   'lake_observation_count','lake_obs_dates', 'unique_dates_count']


# %%% 2.5 Query for lakes w. robust data

# Query lakes that don't have ridiculously large height stdv
# Also get lakes with a sizeable observation count
summary1_robust = summary1.query('lake_height_std < 30 & lake_observation_count > 100 & unique_dates_count > 8')


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
summary1.plot.scatter(x = 'unique_dates_count', y = 'lake_height_std')
summary1_robust.plot.scatter(x = 'unique_dates_count', y = 'lake_height_std')

# %% 3. Plot the distributions of elevation by LakeID
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 3.1 Subset and reformat the data for plotting

# Isolate the best lakes from orgininal IceSat data
robust_lake_pts = lake_pts[lake_pts['area_rank_id'].isin(summary1_robust['area_rank_id'])]

# Join info from robust summary table to the Icesat lake pts. 
robust_lake_pts = pd.merge(robust_lake_pts, 
                           summary1_robust, 
                           how = 'left', 
                           on = 'area_rank_id')

# Make new column for difference from mean for each value
robust_lake_pts['diff_from_mean'] = (robust_lake_pts['height'] - robust_lake_pts['lake_height_mean'])

#!!! Filter lake pts based on the distance from the mean
robust_lake_pts = robust_lake_pts.query('-100 < diff_from_mean < 100')

#!!! Filter lake pts based on year? 
start_date = dt.datetime.strptime('2021-10-01', '%Y-%m-%d').date()
end_date = dt.datetime.strptime('2022-09-30', '%Y-%m-%d').date()

# Filter the DataFrame based on the 'obs_date' column between the defined date range
subset_lake_pts = robust_lake_pts[(robust_lake_pts['obs_date'] > start_date) 
                                  & (robust_lake_pts['obs_date'] < end_date)]


# Subset the data by LakeID for plotting
# Choose the LakeIDs with lowest standard deviation for height. 
subset_LakeIDs = summary1_robust.sort_values('lake_height_std').iloc[0:25]
# Create a series with the lowest standard dev of lake IDs
subset_LakeIDs_series = pd.Series(subset_LakeIDs['area_rank_id'])
# Subset the lake points for plotting
subset_lake_pts = subset_lake_pts[subset_lake_pts['area_rank_id'].isin(subset_LakeIDs_series)]

# Clean up variables
# del(summary1, summary1_robust, lake_pts_icesat)

# %%% 3.2 Make the figure
fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 5
cols = 5
colors_dict = {'frozen': 'grey', 'intermediate_spring': 'green', 
               'liquid': 'blue', 'intermediate_fall': 'red'}

subset_min = subset_lake_pts['diff_from_mean'].min()
subset_max = subset_lake_pts['diff_from_mean'].max()

# Need a list to hold legend patches. 
legend_patches = []

for i, lake_id in enumerate(subset_LakeIDs_series):
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    dataplot = subset_lake_pts[subset_lake_pts['area_rank_id'] == lake_id]
    # Get lake phases for each LakeID
    lake_phases = dataplot['lake_phase_est'].unique()
    # Itereate through lake phases and plot color bars
    plt.xlim(subset_min, subset_max)
    for lake_phase in lake_phases:
        phase_data = dataplot[dataplot['lake_phase_est'] == lake_phase]['diff_from_mean']
        # Generate a histogram
        plt.hist(phase_data, bins = 25, 
                 color = colors_dict.get(lake_phase, 'grey'))

    plt.title(f'Lake = {lake_id}')


plt.tight_layout()
plt.show()


del(i, lake_id, lake_phase, lake_phases, phase_data, 
    rows, cols, colors_dict, dataplot, fig, subset_min, subset_max)
    
# %% 4. Make maps of some lakes. 
# ----------------------------------------------------------------------------
# ============================================================================   

# Not sure how geoplot is better than matplotlib?
map_ID = 'ID_1174'
shape = gsw_lakes.query("area_rank_ == 'ID_1174'")
points = robust_lake_pts.query("area_rank_id == 'ID_1174'")

obs_dates = points['lake_obs_dates'].iloc[0]
marker_styles = ['o', 's', '^', 'D', 'v', 'p', '>', '<', '*', 'h', '+', 'x']

for i, date in enumerate(obs_dates):
    date_pts = points[points['obs_date'] == date] 
    plt.scatter(
        points['geometry'].x,
        points['geometry'].y,
        c = points['height'],
        cmap = 'seismic', 
        label = f'Obs Date: {date}',
        marker = marker_styles[i % len(marker_styles)]
                )
plt.legend(bbox_to_anchor = (1.05, 1), loc = 'upper left')    
plt.colorbar(label = 'Elevation_m')

plt.show()



# %% 5. Write output data for qgis
# ----------------------------------------------------------------------------
# ============================================================================ 

qgis_lakes_out = gsw_lakes[gsw_lakes['area_rank_'].isin(summary1_robust['area_rank_id'])]
qgis_lakes_out = qgis_lakes_out.to_crs('EPSG:3857')

qgis_points_out = robust_lake_pts.to_crs('EPSG:3857')
qgis_points_out['obs_date'] = qgis_points_out['obs_date'].astype(str)
qgis_points_out = qgis_points_out.drop(columns = ['lake_obs_dates'])


qgis_lakes_out.to_file(data_output + 'GSW_robust_lakes.shp',
                       index = False)

qgis_points_out.to_file(data_output + 'GSW_robust_points.shp',
                        index = False)


