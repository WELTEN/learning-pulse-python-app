# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: activities.py
"""

from settings_local import *

# -------------------
#/    ACTIVITIES    /
#-------------------

def df_activities(query):
    # Populating the dataframe
    ACframe = pd.read_gbq(query, LRS_GBQid)
    # Filtering the results 
    ACframe['origin'] = ACframe['origin'].astype(str)
    ACdf = ACframe[['timestamp','objectId','resultDuration']]
    ACdf.rename(columns={'objectId':'App'}, inplace=True)  
    # Grouping steps by sum
    ACrsh = ACdf.groupby(['timestamp', 'App'])['resultDuration'].sum().unstack()
    ACrsh = ACrsh.fillna(0)
    return ACrsh