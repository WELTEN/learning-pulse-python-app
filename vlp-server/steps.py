# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: steps.py
"""

# --------------------
#/    STEPS          /
#--------------------

from core import *

def df_steps(query):
    # Populating the dataframe
    SCframe = pd.read_gbq(query, globe.LRSid) 
     # Filtering the results 
    SCdf = SCframe[['timestamp','resultResponse']]  
    #timestamp as index
    SCrsh = SCdf.set_index(['timestamp']).astype(int) 
    #Rename columns
    SCrsh.rename(columns={'resultResponse':'Steps'}, inplace=True) 
    #Group Step count instances by taking the sum
    SCrsh = SCrsh.groupby(pd.TimeGrouper('5Min'))['Steps'].sum() 
    return SCrsh