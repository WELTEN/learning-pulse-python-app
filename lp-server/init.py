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

def nowFlow():
    # rounded minutes
    rm = (int(datetime.now().strftime('%M'))/5)*5
    timestamp = datetime.now().strftime('%Y-%m-%d %H:')+str(rm)
    df = pd.read_gbq("Select Flow FROM ["+globe.PRStable+"] WHERE timestamp="+timestamp, globe.PRSid)
    return int(df.Flow[0])
   
for i in range (5,6):
    # Fetch and transform User data from the Learning Record Store
    df_original = fetchLRSdata(i,globe.start_first_experiment,globe.end_first_experiment)
    # Smooth values
    df = df_original.loc[:, (df_original != 0).any(axis=0)]
    df = smoothValues(df,True)
    
    # VAR process 
    #--------------------      
    window = 5 # number of timeframe to predict
    results = VARprocess(df)
    forecasts = VARforecast(df,results,window)
    plt = forecasts.ix[-30:,:4].plot()
    plt.axvline(forecasts.index[-5])
    # plot the estimators
    #--------------------    
    #posActivity = 5
    #plot = plots.plot_Residual_corr(df.ix[:,0:maxAttr],results,4,posActivity)   
    
    # Save in BigQuery
    #-------------------- 
    dfSave = forecasts
    dfSave['timestamp'] = forecasts.index
    gbq.to_gbq(dfSave,globe.PRStable,globe.PRSid,if_exists='replace')
    dfLoad = pd.read_gbq("Select * FROM ["+globe.PRStable+"]", globe.PRSid)
    dfLoad = dfLoad.set_index(['timestamp']).sort_index()
    NextFlow = int(dfLoad.Flow[-5])
    dfLoad.Flow[-5:].plot()
    

