# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: heart-rate.py
"""
import core
from core import *

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

def df_heartrate(query):
    """
    # Input: querystring to retrieve the full signal
    # Output: PD dataframe with 5 minute discretised intervals with all the features 
    """
    time1 = time.time()
    HRrsh = pd.DataFrame()
    HRframe = pd.read_gbq(query, globe.LRSid,private_key=globe.LRSkey) # Populating the dataframe
    if len(HRframe)>0:
        HRdf = HRframe[['timestamp','resultResponse','actorId']]
        HRrsh = core.emailToId(HRdf,'actorId')
        HRrsh.set_index(['timestamp','actorId'], inplace=True)
        HRrsh.resultResponse = HRrsh.resultResponse.astype(int)  
        HRrsh = HRrsh.groupby([pd.TimeGrouper('5Min',level=0), 
                           HRrsh.index.get_level_values('actorId')]).agg({'resultResponse': {
        'hr_mean':  np.mean,        # Mean of the signal
        'hr_max':   np.max,         # Maximum
        'hr_min':   np.min,         # Minimum
        'hr_std':   np.std,
        'hr_avc':   avg_change }})['resultResponse']
    
        time2 = time.time()
        print '3 ----- Heartrate feature generation took %0.1f s' % ((time2-time1))
    else:
        print '3 ----- No Heartrate values found in this time-window'
    
    return HRrsh
