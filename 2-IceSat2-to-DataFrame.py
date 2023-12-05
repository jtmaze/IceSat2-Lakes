#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 14:23:54 2023

Generates a pandas csv from HDF5 files

@author: jmaze
"""

# %% 1. Libraries and directories
# ----------------------------------------------------------------------------
# ============================================================================

import icepyx as ipx
from pprint import pprint
import glob
import os
import h5py
import pandas as pd

# !!! Change this line for different local machines
working_dir = '/Users/jmaze/Documents/projects/IceSat2-Lakes'

#Sub folders in larger project. 
data_raw = working_dir + '/data_raw/'
data_intermediate = working_dir + '/data_intermediate/'

# %% 2. Read in the HDF5 files convert to pd.DateFrame
# ----------------------------------------------------------------------------
# ============================================================================

# %%% 2.1 Create a Read object for icepyx to inspect data structure.

# Path to ATL06
ATL06_path = data_raw + 'ATL06'

# Since data was downloaded directly from NSIDC it has the following file name convention 
pattern = "processed_ATL{product:2}_{datetime:%Y%m%d%H%M%S}_{rgt:4}{cycle:2}{orbitsegment:2}_{version:3}_{revision:2}.h5"

# Create a reader object for accessing the files locally
ATL06_reader = ipx.Read(ATL06_path, # Path to data
                        'ATL06', # product 
                         pattern) # Pattern for file detection

# Check out the long list of all variables available.
pprint(ATL06_reader.vars.avail())

# %%%% * icepyx .load is meh...
# Orginally tried icepyx load function, but it does not work. Left for reference. 
# Select the desired variables 
# ATL06_reader.vars.append(var_list = ['h_li', 'latitude', 'longitude'])

# Check out the list of variables as a dictionary
# pprint(ATL06_reader.vars.wanted)

# Read the data.
# ATL06_data = ATL06_reader.load()

# %%% 2.2 Use variable info to make pd.DateFrame

# Bootlegged this code from @jomey on github and adopted it for my own use and variables. 
# https://github.com/ICESAT-2HackWeek/ICESat-2-Hackweek-2023/blob/main/book/tutorials/Hydrology/Hackweek.ipynb

# This nested loop gets very slow if I crank up the dataset size, can I parallelize?
# Might be a way to paralellize this with by turning it into a function

# Use the glob library to match all the file paths into a list. 
file_list = glob.glob(os.path.join(ATL06_path, 'processed_ATL06*.h5'))

# Subset each of the lasers as a group with associated variables. 
file_list_subset = ['gt1l/land_ice_segments/', 'gt1r/land_ice_segments/',
                    'gt2l/land_ice_segments/', 'gt2r/land_ice_segments/',
                    'gt3l/land_ice_segments/', 'gt3r/land_ice_segments/']

# Pull and combine relevant data. 
for index, file_path in enumerate(file_list):
    # Read the data for each file in the larger list. 
    data = h5py.File(file_path, mode = 'r')
    # enumerate will tell how far a long through the loop we are. 
    print(f'File #{index +1}')
    for subgroup in file_list_subset:
        if subgroup in data:
            # Extract the variables of interest from the data for each subgroup and file.
            lat = data.get(os.path.join(subgroup, 'latitude'))
            lon = data.get(os.path.join(subgroup, 'longitude'))
            height = data.get(os.path.join(subgroup, 'h_li'))
            delta_time = data.get(os.path.join(subgroup, 'delta_time'))
            
            # Only keeps subgroups with data
            if all(x is not None for x in [lat, lon, height, delta_time]):
                df = pd.DataFrame(data ={
                    'lat': lat[:],
                    'lon': lon[:],
                    'height': height[:],
                    'delta_time': delta_time[:]})
                # Designate the laser number
                df['laser_id'] = subgroup[:5]
                # Concat the new data frames
                if 'combined_data' not in locals():
                    combined_data = df
                else:
                    combined_data = pd.concat([combined_data, df])    
    # Close the files
    data.close()

# Clean up the environment
del(data, df, lat, lon, delta_time, height, file_list_subset, file_list, pattern, subgroup, 
    ATL06_path, ATL06_reader, index)
    

# %% 3. Write a .csv
# ----------------------------------------------------------------------------
# ============================================================================

combined_data.to_csv(data_intermediate + 'IceSat2_Dataframe_v1.csv')




















                