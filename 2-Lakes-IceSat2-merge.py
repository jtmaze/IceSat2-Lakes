#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 08:56:33 2023

@author: jmaze
"""

# %% 1. Libraries
# ----------------------------------------------------------------------------

import icepyx as ipx
import geopandas as gpd

data_path = '/Users/jmaze/Documents/projects/IceSat2-Lakes/data_raw/'

# %% 2. Import the IceSat2 and Greenland Lakes data
# ----------------------------------------------------------------------------

# %%% 2.1 Import the Lakes
gr_lakes = gpd.read_file(data_path + 'Greenland_IIML_2017.shp')

gr_lakes.attrs

# %%% 2.2 Import the IceSat2

