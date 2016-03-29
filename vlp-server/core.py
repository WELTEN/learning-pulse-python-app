# -*- coding: utf-8 -*-
"""
@author: Daniele Di Mitri ddm@ou.nl
@title: core.py
"""

import numpy as np
import pandas as pd
import time
#from datetime import datetime, timedelta
import globe
import ratings
import steps
import heartrate
import activities
import weather
from statsmodels.tsa.api import VAR



#  CORE FUNCTIONS
#**************************
# Fuction name: fetchLRSdata
# Description: takes the LRS data 
# Input: non smoothed dataframe
# Output: smoothed dataframe 
#-------------------------------------    
def fetchLRSdata(userid,start_date,end_date):

    actorID =  "'mailto:arlearn"+str(userid)+"@gmail.com'"  
    
    # Ratings
    query = "SELECT *  FROM "+globe.LRStable+" WHERE " \
        "origin = 'rating' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfRT = ratings.df_ratings(query)
    
    # Steps
    query = "SELECT *  FROM "+globe.LRStable+" WHERE " \
        "objectID = 'StepCount' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfSC = steps.df_steps(query)
    
    # Heart Rate
    query = "SELECT *  FROM "+globe.LRStable+" WHERE " \
        "objectID = 'HeartRate' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfHR = heartrate.df_heartrate(query) 
    
    # Activities
    query = "SELECT *  FROM "+globe.LRStable+" WHERE " \
        "origin = 'rescuetime' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"')  AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfAC = activities.df_activities(query)
    
    # Weather
    #@todo need to change this method
    weather_file = "weather_data.csv"
    dfWT = weather.df_weather(weather_file)
    
    # --------------------
    #/    MERGE          /
    #--------------------  
    # Add Ratings
    DF = pd.concat([dfRT.resample('5Min').fillna(method='pad'),dfHR,dfSC],axis=1)
    
    # The timeframes where there are no rating are DROPPED
    DF =  DF.dropna()    
    
    # Join LEFT with the Activity data
    DF = DF.join(dfAC,how='left') #inner join method
    DF = DF.loc[:, (DF != 0).any(axis=0)] # drop columns with all zeros
    
    # Join LEFT the weather data     
    DF = DF.join(dfWT.resample('5Min').fillna(method='pad'),how='left')
    
     # The timeframes where there is no RescueTime data are FILLED di0 
    DF =  DF.fillna(0) 

    return DF


# Fuction name: smoothValues
# Description: Values smoothing with Exponential Weighted Moving Average
# http://pandas.pydata.org/pandas-docs/stable/generated/pandas.ewma.html
# Input: non smoothed dataframe
# Output: smoothed dataframe 
#-------------------------------------    
def smoothValues(df,ignoreCategorical):
      
    span = 12  #Center of Mass com =  (span - 1)/2
    
    # helper dataframe
    dfEWMA = pd.DataFrame() 
    # The columns to smooth
    Y_names = ['Abilities','Challenge','Productivity','Stress','MainActivity']
    
    X_namesCat = ['MainActivity','Conditions']
   
   # The columns not to smooth
    if ignoreCategorical:    
        X_names =  [col for col in df.columns if col not in (Y_names and X_namesCat)]   
    else:
        X_names =  [col for col in df.columns if col not in Y_names]   
 
    # Loop trhough each day and apply EWMA treating each day individually
    # Append the smoothed values in the helper dataframe dfEWMA
    for g in df.groupby([df.index.year,df.index.month,df.index.day]):
        dfEWMA = dfEWMA.append(pd.ewma(g[1],span=span))  
    # Order the loop
    dfEWMA.sort_index(inplace=True)
    
    # Fill the null values with 0
    dfEWMA.fillna(0,inplace=True)
    
    df[X_names] = dfEWMA[X_names]
    
    #Remove the cold start instances! i.e. when the instances Rescue Time data
    # all sums up to 0
    df = df[(df[X_names].T!=0).any()]
    
    return df
    
def VARprocess(df,log):
    # Log transformation, relative difference and drop NULL values
    if (log):    
        dfLogDiff = np.log(df).diff().dropna()
    else:
        dfLogDiff = df
    # Vector Autoregression Process generation    
    #print dfLogDiff
    VARmodel = VAR(dfLogDiff)
    # Model fitting 
    #@todo check lag order selection
    results = VARmodel.fit(maxlags=50, ic='aic')
    return results
    
def VARforecast(df,results,window,log):
    lag_order = results.k_ar
    # Generate n prediction, where n is the window size, return array
    forecasts = results.forecast(df.values[-lag_order:], window)
    # Create the new index for the predictions
    ixPred = pd.date_range(df[-1:].index.to_pydatetime()[0]
        .strftime("%Y-%m-%d %H:%M:%S"),periods=window+1,freq='5min')
    ixPred = ixPred[-window:] #delete the first which exists
    # Generate a dataframe
    dfForecasts = pd.DataFrame(forecasts,index=ixPred,columns=df.columns.values)
    # Append the forecast to the original set, then add the header of the df
    # Invert the logarithmic scale and apply cumsum
    #dfReturn = np.exp(pd.concat([np.log(df)[:1],
    #                             dfLogDiff.append(dfForecasts)]).cumsum())
    dfReturn = df.append(dfForecasts)
    return dfReturn
    