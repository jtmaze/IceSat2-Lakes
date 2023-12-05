#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 11:54:00 2023

@author: jmaze
"""


# %% 1. Libraries and directories
# ----------------------------------------------------------------------------
# ============================================================================

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import seaborn as sns
import numpy as np

# !!! Change this for different local machines
working_dir = '/Users/jmaze/Documents/projects/IceSat2-Lakes'
data_output = working_dir + '/data_output/'
data_intermediate = working_dir + '/data_intermediate/'

# %% 2. Read IceSatPts and LakesGSWE
# ----------------------------------------------------------------------------
# ============================================================================

# Read the lake boundaries
LakesGSWE = gpd.read_file(data_intermediate + 'LakesGSWE_v2.shp')

# Read the IceSat-2 points associated with GSWE lakes
IceSatPts = gpd.read_file(data_intermediate + 'IceSat2_pts_GSWE.shp')
IceSatPts.drop(columns = 'index_righ', inplace = True)

# Since shapefile format truncates at 10 characters, rename the column. 
IceSatPts.rename(columns = {'area_rank_': 'area_rank_id', 'height': 'z'}, inplace = True)
LakesGSWE.rename(columns = {'area_rank_': 'area_rank_id', 'height': 'z'}, inplace = True)

# %% 3. Add obs_date and wtr_yr columns
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 3.1 Create a obs_date from delta_time

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
IceSatPts = IceSatPts.assign(obs_date = IceSatPts['delta_time'].apply(calendar_from_delta))

# %%% 3.2 Create a wtr_yr from obs_date

def wtr_yr_from_calendar (obs_date):
    # Designate wtr_yr based on month
    if obs_date.month >= 10:
        wtr_yr = obs_date.year + 1
    else: 
        wtr_yr = obs_date.year
    # Return water year as string??    
    return(f'WY{wtr_yr}')


# Run the function
IceSatPts = IceSatPts.assign(wtr_yr = IceSatPts['obs_date'].apply(wtr_yr_from_calendar))

# %% 4. Group by daf
# ----------------------------------------------------------------------------
# ============================================================================

# sns.histplot(data = IceSatPts, x = 'z', bins = 100, log_scale = True)
# plt.xscale('log')
# plt.show()

# Remove the worst IceSat2 points there's pts with elevation above Greenland's 
# maximum, almost 170,239 of these.
n = len(IceSatPts.query('z > 10000'))
IceSatPts.query('z < 10000', inplace = True)

Summary = IceSatPts.groupby(['area_rank_id', 'wtr_yr'], as_index = False).agg(
    z_mean = ('z', 'mean'),
    z_std = ('z', 'std'),
    obs_count = ('area_rank_id', 'size'),
    area_m2 = ('area_m2', 'first'),
    obs_date_unique = ('obs_date', lambda x: len(x.unique().astype(str).tolist()))
    )


# %% 5. Visualize Summary Stats and Apply Thresholding
# ----------------------------------------------------------------------------
# ============================================================================

# Set thresholding 
SummaryRobust = Summary.query('z_std < 30 & obs_count > 25 & obs_date_unique > 2')

# Make column
is_robust = Summary[['area_rank_id', 'wtr_yr']].isin(SummaryRobust[['area_rank_id', 'wtr_yr']])
Summary['is_robust'] = is_robust.all(axis = 1)

# Visualize the diffences between robust and non-robust points
scatter = sns.scatterplot(x = Summary['area_m2'], y = Summary['z_std'],
                          s = 5, hue = Summary['is_robust'], palette = 'Set2')
# Work on the axes
plt.yscale('log')
plt.xlabel('Log of lake area (square kilometers)')
plt.xscale('log')
plt.ylabel('Log of segments standard deviation by lake (m)')
plt.title('Relationship between Lake Area and Segment Variability')

# How many lakes are in the robust dataset
(SummaryRobust['area_rank_id'].nunique)

# %% 6. Join the IceSat points to Summary Stats
# ----------------------------------------------------------------------------
# ============================================================================

IceSatPtsRobust = pd.merge(IceSatPts, 
                            SummaryRobust, 
                            how = 'inner', 
                            on = ['area_rank_id', 'wtr_yr', 'area_m2'])

# Create diff from mean column
IceSatPtsRobust['z_diff_from_lake_mean'] = IceSatPtsRobust['z'] - IceSatPtsRobust['z_mean']

# %% 6. Subset IceSat2 Points for Plotting
# ----------------------------------------------------------------------------
# ============================================================================

SubsetPts = IceSatPtsRobust.query("wtr_yr == 'WY2022'")

shuffled_summary = SummaryRobust.query("wtr_yr == 'WY2022'")

shuffled_summary = shuffled_summary.sample(n = 25, random_state = 42)
shuffled_summary = pd.Series(shuffled_summary['area_rank_id'])

SubsetPts2 = SubsetPts[SubsetPts['area_rank_id'].isin(shuffled_summary)]

# %% 6. Make a plot
# ----------------------------------------------------------------------------
# ============================================================================

# fig = plt.figure(figsize=[12, 8])
# # Designate number of cols and rows
# rows = 5
# cols = 5

# # Eliminate outlier points
# SubsetPts2.query('-5 < z_diff_from_lake_mean < 5', inplace = True)

# for i, lake_id in enumerate(shuffled_summary):
    
#     #Specify the subplot
#     plt.subplot(rows, cols, i + 1)
#     # Match data to current Lake_ID
#     DataPlot = SubsetPts2[SubsetPts2['area_rank_id'] == lake_id]
#     # Get the observation dates for each LakeID
#     obs_dates = DataPlot['obs_date'].unique()
#     # Itereate through lake phases and plot color bars
#     sns.histplot(data = DataPlot, x = 'z_diff_from_lake_mean', hue = 'obs_date', bins = 50,
#                  multiple = 'stack', palette = 'Dark2', legend = False)
#     plt.title(f'Lake = {lake_id}')
    
# plt.tight_layout()
# plt.show()


# ____________________________________________________________

# Eliminate outlier points
SubsetPts2 = SubsetPts2.query('-5 < z_diff_from_lake_mean < 5').copy()

 # !!! Change wy_start and wy_end accordingly
wy_start = dt.date(2021, 10, 1)
wy_end = dt.date(2022, 9, 30)
wy_total = (wy_end - wy_start).days
date_range = [wy_start + dt.timedelta(days = x) for x in range(wy_total + 1)]
 
# Make a scaling function to color obs dates
def scale_date_wynumber(obs_date):
    
    # Count days since wy_start
    days_diff = (obs_date - wy_start).days
    day_rank = days_diff % wy_total + 1
    
    return(day_rank)

fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 5
cols = 5


for i, lake_id in enumerate(shuffled_summary):
    
    #Specify the subplot
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    DataPlot = SubsetPts2[SubsetPts2['area_rank_id'] == lake_id]
    # Get the observation dates for each LakeID
    DataPlot['day_rank'] = DataPlot['obs_date'].apply(scale_date_wynumber)
    # Itereate through lake phases and plot color bars
    sns.histplot(data = DataPlot, x = 'z_diff_from_lake_mean', hue = 'day_rank', bins = 50,
                 multiple = 'stack', palette = 'viridis', alpha = 0.7, legend = False)
    plt.xlabel(None)
    plt.ylabel(None)
    plt.title(f'Lake = {lake_id}')
    
    
# Color bar legend
cax = plt.axes([0.05, # left
                0.2, # bottom
                0.03, # width
                0.5])  # height
sm = plt.cm.ScalarMappable(cmap = 'viridis')  # Define a scalar mappable
sm.set_array([])  # Set an empty array to the scalar mappable
fig.colorbar(sm, cax=cax, orientation= 'vertical').set_ticks([])  # Add colorbar with label

plt.show()

# Plot single lake

OneLakePts = IceSatPtsRobust.query("area_rank_id == 'ID_230'")
OneLakePts = OneLakePts.query('-5 < z_diff_from_lake_mean < 5 & wtr_yr == "WY2022"').copy()

sns.histplot(data = OneLakePts, x = 'z', bins = 25, hue = 'obs_date', 
             multiple = 'stack', palette = 'Dark2')
plt.title('Water Year 2022')
plt.xlabel('Elevation (m)')
plt.show()










