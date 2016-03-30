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
    # VAR process activation
    results,maxAttr = VARprocess(df,log=False)
    # predictions
    window = 5 # number of timeframe to predict
    forecasts = VARforecast(df.ix[:,0:maxAttr],results,window,False)
    # plot the estimators
    posActivity = 5
    plot = plots.plot_Residual_corr(df.ix[:,0:maxAttr],results,4,posActivity)   
    
    #results.tvalues.ix[:,4]
    
    # Save in BigQuery
    print "fake saving..."
    #dfPredData.to_gbq(PRSid, PRStable) 