# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: steps.py
"""

# --------------------
#/    STEPS          /
#--------------------
import core
from core import *

def df_steps(query,allUsers=False):
    # Populating the dataframe
    time1 = time.time()
    SCframe = pd.read_gbq(query, globe.LRSid) 
    SCrsh = pd.DataFrame()
    if len(SCframe)>0:
         # Filtering the results 
        SCdf = SCframe[['timestamp','resultResponse','actorId']] 
        SCrsh = core.emailToId(SCdf,'actorId')
        #Rename columns
        SCrsh.rename(columns={'resultResponse':'Steps'}, inplace=True)
        SCrsh.Steps = SCrsh.Steps.astype(int)        
        SCrsh.set_index(['timestamp','actorId'], inplace=True)
        SCrsh = SCrsh.groupby([pd.TimeGrouper('5Min',level=0), SCrsh.index.get_level_values('actorId')])['Steps'].sum()
        time2 = time.time()  
        print '----- Steps values read from BigQuery in %0.3f s' % ((time2-time1))
    return SCrsh