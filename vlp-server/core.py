# -*- coding: utf-8 -*-
"""
@author: Daniele Di Mitri ddm@ou.nl
@title: core.py
"""

import numpy as np
import pandas as pd
#from datetime import datetime, timedelta
import ConfigParser

import ratings
import steps
import heartrate
import activities
import weather

from statsmodels.tsa.api import VAR


#  GLOBAL VARIABLES
#**************************

# Get configuration file
configParser = ConfigParser.RawConfigParser()
configFilePath = r'/Users/daniele/Documents/VisualLearningPulse/code/settings.config'
configParser.read(configFilePath)

# Learning Record store id
LRSid = configParser.get('vlp', 'lrs_id')
# LRS tablename
LRStable = configParser.get('vlp', 'lrs_table')
# Prediction Record store id
PRSid = configParser.get('vlp', 'prs_id')
# LRS tablename
PRStable = configParser.get('vlp', 'prs_table')


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
    query = "SELECT *  FROM "+LRStable+" WHERE " \
        "origin = 'rating' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfRT = ratings.df_ratings(query)
    
    # Steps
    query = "SELECT *  FROM "+LRStable+" WHERE " \
        "objectID = 'StepCount' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfSC = steps.df_steps(query)
    
    # Heart Rate
    query = "SELECT *  FROM "+LRStable+" WHERE " \
        "objectID = 'HeartRate' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfHR = heartrate.df_heartrate(query) 
    
    # Activities
    query = "SELECT *  FROM "+LRStable+" WHERE " \
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
    #@todo ActivityType
    DF = pd.concat([dfRT,dfSC,dfHR],axis=1)
                    
    # Fill the NULL values in Ratings BACKWARD
    DF[['Abilities','Challenge','Productivity','Stress',
        'ActivityType']].fillna(method='bfill',inplace=True)
    
    # Delete all the head values which are still NULL
    DF = DF.dropna()
    
    # Join LEFT with the Activity data
    DF = DF.join(dfAC,how='left') #inner join method
    
    # Join LEFT the weather data     
    DF = DF.join(dfWT,how='left')
    
    # Fill the NULL values FORWARD
    DF[['Temp',
        'Humidity','Pressure','Conditions']].fillna(method='pad',inplace=True)
    
    return DF


# Fuction name: smoothValues
# Description: Values smoothing with Exponential Weighted Moving Average
# http://pandas.pydata.org/pandas-docs/stable/generated/pandas.ewma.html
# Input: non smoothed dataframe
# Output: smoothed dataframe 
#-------------------------------------    
def smoothValues(df):
      
    span = 12  #Center of Mass com =  (span - 1)/2
    
    # helper dataframe
    dfEWMA = pd.DataFrame() 
    # The columns to smooth
    dontSmoothCols = ['Abilities','Challenge','Productivity','Stress',
        'ActivityType','Conditions']
    # The columns not to smooth
    smoothCols =  [col for col in df.columns if col not in dontSmoothCols]   
    
    # Loop trhough each day and apply EWMA treating each day individually
    # Append the smoothed values in the helper dataframe dfEWMA
    for g in df.groupby([df.index.year,df.index.month,df.index.day]):
        dfEWMA = dfEWMA.append(pd.ewma(g[1],span=span))  
    # Order the loop
    dfEWMA.sort_index(inplace=True)
    
    # Fill the null values with 0
    dfEWMA.fillna(0,inplace=True)
    
    df[smoothCols] = dfEWMA[smoothCols]
    
    #Remove the cold start instances! i.e. when the instances Rescue Time data
    # all sums up to 0
    df = df[(df[smoothCols].T!=0).any()]
    
    return df
    
def VARprocess(df,window):
    # Log transformation, relative difference and drop NULL values
    dfLogDiff = np.log(df).diff().dropna()
    # Vector Autoregression Process generation    
    VARmodel = VAR(dfLogDiff)
    # Model fitting 
    #@todo check lag order selection
    results = VARmodel.fit(maxlags=15, ic='aic')
    lag_order = results.k_ar
    # Generate n prediction, where n is the window size, return array
    forecasts = results.forecast(dfLogDiff.values[-lag_order:], window)
    # Create the new index for the predictions
    ixPred = pd.date_range(dfLogDiff[-1:].index.to_pydatetime()[0]
        .strftime("%Y-%m-%d %H:%M:%S"),periods=window+1,freq='5min')
    ixPred = ixPred[-ixPred:] #delete the first which exists
    # Generate a dataframe
    dfForecasts = pd.DataFrame(forecasts,index=ixPred,columns=df.columns.values)
    # Append the forecast to the original set, then add the header of the df
    # Invert the logarithmic scale and apply cumsum
    dfReturn = np.exp(pd.concat([np.log(df)[:1],
                                 dfLogDiff.append(dfForecasts)]).cumsum())
    
    return dfReturn    
