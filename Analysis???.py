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
import pprint

# !!! Change this for different local machines
working_dir = '/Users/jmaze/Documents/projects/IceSat2-Lakes'
data_output = working_dir + '/data_output/'

# %% 2. Read the data and explore basic attributes
# ----------------------------------------------------------------------------
# ============================================================================

lake_pts_icesat = gpd.read_file(data_output + 'lake_pts_icesat.shp')

# How many lakes are we looking at per lake?
(lake_pts_icesat['LakeID'].value_counts())

# Plot the distribution of elevation values by lake
lake_info = lake_pts_icesat.groupby(by = 'LakeID').describe('height')
print(lake_info)