# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: activities.py
"""

from core import *

# -------------------
#/    ACTIVITIES    /
#-------------------

def df_activities(query):
    # Populating the dataframe
    time1 = time.time()
    ACframe = pd.read_gbq(query, globe.LRSid)
    # Filtering the results 
    ACframe['origin'] = ACframe['origin'].astype(str)
    ACdf = ACframe[['timestamp','objectId','resultDuration']]
    ACdf.rename(columns={'objectId':'App'}, inplace=True)  
    # Grouping steps by sum
    ACrsh = ACdf.groupby(['timestamp', 'App'])['resultDuration'].sum().unstack()
    # Fill null values
    ACrsh = ACrsh.fillna(0)
    ACrsh = ACrsh[ACrsh.sum().sort_values(ascending=False).index.tolist()]
    ACrsh = ACrsh.loc[:,ACrsh.var()>10]         
    time2 = time.time()  
    print 'Activity values read from BigQuery in %0.1f s' % ((time2-time1))
    return ACrsh