# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: heart-rate.py
"""

from settings_local import *

# --------------------
#/    HEART-RATE     /
#--------------------

# Calculate the duration of the most positive run (strictly monotonic)
def long_pos_run(y):
    if y.empty:
        return None
    else:
        y = (y > y.shift()) 
        return max(y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1))

# Calculate the duration of the most negative run (strictly antimonotonic)
def long_neg_run(y):
    if y.empty:
        return None
    else:
        y = (y < y.shift()) 
        return max(y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1)) 

# Calculates the average of the change 
def avg_change(y):
    return y.diff().abs().mean()

# Argmin modified to handle the Null values
def _argmin(y):
    if y.empty:
        return None
    else:
        return y.argmin()
        
# Argmax modified to handle the Null values
def _argmax(y):
    if y.empty:
        return None
    else:
        return y.argmax()

# List of the Heart rate features        
hr_features = {
    'hr_mean':  np.mean,        # Mean of the signal
    'hr_max':   np.max,         # Maximum
    'hr_min':   np.min,         # Minimum
    'hr_std':   np.std,         # Standard Deviation
    'hr_avc':   avg_change,     # Average change
    'hr_lpr':   long_pos_run,   # Long positive run
    'hr_lnr':   long_neg_run    # Long negative run
#   'hr_amax':  _argmax,        # Loc in index of the Max
#   'hr_ain':  _argmin          # Loc in index of the Min
}    

# Fuction name: df_heartrate 
# Input: querystring to retrieve the full signal
# Output: PD dataframe with 5 minute discretised intervals with all the features 
def df_heartrate(query):
    
    time1 = time.time()
    HRframe = pd.read_gbq(query, LRS_GBQid) # Populating the dataframe
    HRdf = HRframe[['timestamp','resultResponse']]
    signal = HRdf.set_index(['timestamp']).astype(int)  #timestamp as index    
    time2 = time.time()  
    print 'Heart rate value read from BigQuery in %0.3f ms' % ((time2-time1)*1000)
    
    time1 = time.time()
    hr_df = pd.DataFrame()
    
    for group in signal.groupby([signal.index.year,signal.index.month,signal.index.day]):
        hr_df = hr_featured.append(group[1].resample('5Min', how={'resultResponse': hr_features}))
    time2 = time.time()
    print 'Heart rate feature generation took %0.3f ms' % ((time2-time1)*1000)
    return hr_df