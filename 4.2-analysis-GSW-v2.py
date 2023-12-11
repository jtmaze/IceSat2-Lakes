#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  4 11:54:00 2023

@author: jmaze
"""


# %% 1. Libraries and directorie s
# ----------------------------------------------------------------------------
# ============================================================================

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import seaborn as sns

# !!! Change this for different local machines
working_dir = '/Users/jtmaz/Documents/projects/IceSat2-Lakes'
data_output = working_dir + '/data_output/'
data_intermediate = working_dir + '/data_intermediate/'

# %% 2. Read IceSatPts and LakesGSWO
# ----------------------------------------------------------------------------
# ============================================================================

# Read the lake boundaries
LakesGSWO = gpd.read_file(data_intermediate + 'LakesGSWO_v2.shp')

# Read the IceSat-2 points associated with GSWO lakes
IceSatPts = gpd.read_file(data_intermediate + 'IceSat2_pts_GSWO.shp')

# Since shapefile format truncates at 10 characters, rename the column. 
# Also calling height 'z'
IceSatPts.rename(columns = {'area_rank_': 'area_rank_id', 'height': 'z'}, inplace = True)
LakesGSWO.rename(columns = {'area_rank_': 'area_rank_id', 'height': 'z'}, inplace = True)

# %% 3. Add obs_date and wtr_yr columns
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 3.1 Create a obs_date from delta_time

# Per this documentation:
# https://nsidc.org/sites/default/files/icesat2_atl06_data_dict_v003_0.pdf
# delta_time is the number of seconds since 2018-01-01

# Writing a function and using the .apply method should make this faster for large data. 
def calendar_from_delta (delta_time):
    
    # Make a datetime object based on the ATL06 epoch
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

# %% 4. Group by area_rank_id and wtr_yr
# ----------------------------------------------------------------------------
# ============================================================================

# sns.histplot(data = IceSatPts, x = 'z', bins = 100, log_scale = True)
# plt.xscale('log')
# plt.show()

# Remove the worst IceSat2 points there's pts with elevation above Greenland's 
# maximum, almost 170,239 of these.
n = len(IceSatPts.query('z > 10000'))
del(n)
IceSatPts.query('z < 10000', inplace = True)

Summary = IceSatPts.groupby(['area_rank_id', 'wtr_yr'], as_index = False).agg(
    z_mean = ('z', 'mean'),
    z_std = ('z', 'std'),
    obs_count = ('z', 'count'),
    area_m2 = ('area_m2', 'first'),
    obs_dates_list = ('obs_date', lambda x: x.unique().astype(str).tolist()),
    obs_date_unique = ('obs_date', lambda x: len(x.unique().astype(str).tolist()))
    )

# %% 5. Visualize Summary Stats and Apply Thresholding
# ----------------------------------------------------------------------------
# ============================================================================

# Set thresholding to balance variability and amount of observations
SummaryRobust = Summary.query('z_std < 50 & obs_count > 25 & obs_date_unique > 3')

# Make column denoting the robust threshold. 
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

# Clean up the vars
del(is_robust, scatter)

# %% 6. Join the IceSatPts to SummaryRobust
# ----------------------------------------------------------------------------
# ============================================================================

IceSatPtsRobust = pd.merge(IceSatPts, 
                            SummaryRobust, 
                            how = 'inner', 
                            on = ['area_rank_id', 'wtr_yr', 'area_m2'])

# %%% 6.1 Make a difference from lake mean column to improve plotting

# Create diff from mean column
IceSatPtsRobust['z_diff_from_lake_mean'] = IceSatPtsRobust['z'] - IceSatPtsRobust['z_mean']

# %% 7. Subset IceSat2 Points for Plotting
# ----------------------------------------------------------------------------
# ============================================================================

SubsetPts = IceSatPtsRobust.query("wtr_yr == 'WY2021'")

# Randomly select 25 Lakes from the robust data for plotting
shuffled_summary = SummaryRobust.query("wtr_yr == 'WY2021'")
shuffled_summary = shuffled_summary.sample(n = 25, random_state = 42)
shuffled_summary = pd.Series(shuffled_summary['area_rank_id'])

SubsetPts = SubsetPts[SubsetPts['area_rank_id'].isin(shuffled_summary)]

# %% 8. Make 25-panel plot of random lakes
# ----------------------------------------------------------------------------
# ============================================================================

# %%% Manipulate data for plotting

# Eliminate outlier points for plot scales
SubsetPts = SubsetPts.query('-5 < z_diff_from_lake_mean < 5').copy()

 # !!! Change wy_start and wy_end accordingly
wy_start = dt.date(2020, 10, 1)
wy_end = dt.date(2021, 9, 30)
wy_total = (wy_end - wy_start).days
date_range = [wy_start + dt.timedelta(days = x) for x in range(wy_total + 1)]
 
# Make a scaling function to color obs dates
def scale_date_wynumber(obs_date):
    # Count days since wy_start
    days_diff = (obs_date - wy_start).days
    day_rank = days_diff % wy_total + 1
    
    return(day_rank)

# %%% Generate the plot

fig = plt.figure(figsize=[12, 8])
# Designate number of cols and rows
rows = 5
cols = 5

for i, lake_id in enumerate(shuffled_summary):
    #Specify the subplot
    plt.subplot(rows, cols, i + 1)
    # Match data to current Lake_ID
    DataPlot = SubsetPts[SubsetPts['area_rank_id'] == lake_id]
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

# Clean up loose vars
del(i, n, rows, cols, sm, SubsetPts, wy_end, wy_start, wy_total, lake_id, fig,
    date_range, cax, DataPlot, shuffled_summary)

# %% 9. Plot histograms for a single lake
# ----------------------------------------------------------------------------
# ============================================================================

OneLakePts = IceSatPtsRobust.query("area_rank_id == 'ID_230'")
OneLakePts = OneLakePts.query('-5 < z_diff_from_lake_mean < 5 & wtr_yr == "WY2022"').copy()

sns.histplot(data = OneLakePts, x = 'z', bins = 25, hue = 'obs_date', 
             multiple = 'stack', palette = 'Dark2')
plt.title('Water Year 2022')
plt.xlabel('Elevation (m)')
plt.show()

# Clean up loose vars
del(OneLakePts)

# %% 10. Make a map for a single lake
# ----------------------------------------------------------------------------
# ============================================================================

Lake = LakesGSWO.query("area_rank_id == 'ID_230'")
lake_geometry = Lake['geometry'].iloc[0]
Points = IceSatPtsRobust.query("area_rank_id == 'ID_230'")

obs_dates = Points['obs_dates_list'].iloc[0]
marker_styles = ['*', 's', '+', 'X', 'O']
# Points = Points.query('obs_date == ""')

for i, date in enumerate(obs_dates):
    date_pts = Points[Points['obs_date'] == date] 
    plt.scatter(
        Points['geometry'].x,
        Points['geometry'].y,
        c = Points['z_diff_from_lake_mean'],
        cmap = 'seismic',
        label = f'Obs Date: {date}',
        s = 5,
        marker = marker_styles[i % len(marker_styles)])
    plt.fill(lake_geometry.exterior.xy[0], lake_geometry.exterior.xy[1], 
             facecolor='none', edgecolor='purple')
plt.legend(bbox_to_anchor = (1.05, 1), loc = 'upper left')    
plt.colorbar(label = 'Elevation_m')

plt.show()

# Clean up variables
del(Lake, Points, obs_dates, i, lake_geometry, date_pts, date)

# %% 11. Write robust lakes and points to output folder. 
# ----------------------------------------------------------------------------
# ============================================================================

# %%% Reproject and points and reformat cols to be shapefile compatible

LakesOut = LakesGSWO[LakesGSWO['area_rank_id'].isin(SummaryRobust['area_rank_id'])]
LakesOut = LakesOut.to_crs('EPSG:3857')

PtsOut = IceSatPtsRobust.to_crs('EPSG:3857')
PtsOut['obs_date'] = PtsOut['obs_date'].astype(str)
PtsOut = PtsOut.drop(columns = ['obs_dates_list'])

# %%% Write to output directory
LakesOut.to_file(data_output + 'GSWO_robust_lakes.shp',
                       index = False)

PtsOut.to_file(data_output + 'GSWO_robust_points.shp',
                        index = False)

# %% ** Scratch work
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








