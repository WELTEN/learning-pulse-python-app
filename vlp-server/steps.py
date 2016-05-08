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
    SCframe = pd.read_gbq(query, globe.LRSid) 
     # Filtering the results 
    SCdf = SCframe[['timestamp','resultResponse','actorId']] 
    SCrsh = core.emailToId(SCdf,'actorId')
    #Rename columns
    SCrsh.rename(columns={'resultResponse':'Steps'}, inplace=True)
    SCrsh.Steps = SCrsh.Steps.astype(int)        
    SCrsh.set_index(['timestamp','actorId'], inplace=True)
    SCrsh = SCrsh.groupby([pd.TimeGrouper('5Min',level=0), SCrsh.index.get_level_values('actorId')])['Steps'].sum()
    return SCrsh