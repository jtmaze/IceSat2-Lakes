#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov  7 16:22:06 2023

IceSat2 download script

@author: jmaze
"""

# %% 1. Libraries
# ----------------------------------------------------------------------------

import icepyx as ipx

download_path = '/Users/jmaze/Documents/projects/IceSat2-Lakes/data_raw'

# %% 2. Download

begining = '2022-11-01'
end = '2023-03-01'
time = [begining, end]
bound_box = [ 31.966824, -1.833499, 33.875129, -0.495605] 
# Switch to somewhere in Western Greenland

# Pick spatial and temporal attributes
ds_identifier = ipx.Query(product = 'ATL06', 
                          spatial_extent = bound_box,
                          date_range = time)


ds_identifier.order_granules()

ds_identifier.download_granules(path = download_path)



ds_identifier.earthdata_login('jmaze', 'jmaze@uoregon.edu')