# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: init.py
"""
from core import *
import globe
import plots

# Import global names
globe.setGlobalNames()


for i in range (7,8):
    # Fetch and transform User data from the Learning Record Store
    df = fetchLRSdata(i,globe.start_first_experiment,globe.end_first_experiment)
    # Smooth values
    df = df.loc[:, (df != 0).any(axis=0)]
    df = smoothValues(df,True)
    # Activate VAR process
    window = 5 # number of timeframe to predict
    # Set the maximum number of attributes to be considered for VAR
    no_attr = 40    
    # VAR process activation
    results = VARprocess(df.ix[:,0:no_attr],False)
    # predictions
    forecasts = VARforecast(df.ix[:,0:no_attr],results,window,False)
    # plot the estimators
    posActivity = 5
    plot = plots.plot_Residual_corr(df.ix[:,0:no_attr],results,4,posActivity)   
    
    print results.tvalues.ix[:,4]
    
    # Save in BigQuery
    print "fake saving..."
    #dfPredData.to_gbq(PRSid, PRStable) 