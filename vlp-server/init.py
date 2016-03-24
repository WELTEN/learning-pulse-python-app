# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: init.py
"""
from core import *

start_first_experiment = '2015-11-23 07:00:00'
end_first_experiment = '2015-12-09 20:00:00'

for i in range (7,8):
    # Fetch and transform User data from the Learning Record Store
    dfUserData = fetchLRSdata(i,start_first_experiment,end_first_experiment)
    # Smooth values
    dfUserData = smoothValues(dfUserData)
    # Activate VAR process
    dfPredData = VARprocess(dfUserData)
    # Save in BigQuery
    dfPredData.to_gbq(PRSid, PRStable) 
    

    