# -*- coding: utf-8 -*-
"""
@author: Daniele Di Mitri ddm@ou.nl
@title: core.py
"""

import numpy as np
import pandas as pd
import time
from datetime import datetime
import operator
#from datetime import datetime, timedelta
import globe
import ratings
import steps
import heartrate
import activities
import weather
from statsmodels.tsa.api import VAR
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pandas.io import gbq
import sys

#  CORE FUNCTIONS
def fetchData(start_date,end_date):
    """
    Description: this function is responsible to the 
    Input: the datetime to query the db
    Output: the datetime 
    """
    
    # Ratings
    query = "SELECT *  FROM "+globe.LRStable+" WHERE origin = 'rating' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfRT = ratings.df_ratings(query)
    
    # Steps
    query = "SELECT *  FROM "+globe.LRStable+" WHERE objectID = 'StepCount' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfSC = steps.df_steps(query)
    
    # Heart Rate
    query = "SELECT *  FROM "+globe.LRStable+" WHERE objectID = 'HeartRate' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfHR = heartrate.df_heartrate(query) 
    
    # Activities
    query = "SELECT *  FROM "+globe.LRStable+" WHERE origin = 'rescuetime' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"')  AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfAC,dfCA = activities.df_activities(query)
    
    # Weather
    query = "SELECT *  FROM "+globe.weather_table+" WHERE " \
        " date > PARSE_UTC_USEC('"+start_date+"')  AND date < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by date"
    dfWT = weather.df_weather(query)
    
    # --------------------
    #/    MERGE          /
    #--------------------  
    # Add Ratings        
    DF =  dfRT.dropna().join([dfSC,dfWT]).fillna(0)   
    
    # Join LEFT the weather data     
    DF = DF.join(dfHR).dropna()
    
    # Join the Categories     
    DF = DF.join(dfCA).dropna()

    return DF

def smoothValues(df,ignoreCategorical):

    """
    Description: Values smoothing with Exponential Weighted Moving Average
    http://pandas.pydata.org/pandas-docs/stable/generated/pandas.ewma.html
    Input: non smoothed dataframe
    Output: smoothed dataframe 
    """
      
    span = 12  #Center of Mass com =  (span - 1)/2
    
    # helper dataframe
    dfEWMA = pd.DataFrame() 
    # The columns to smooth
    Y_names = ['Abilities','Challenge','Productivity','Stress', 'Flow', 
               'MainActivity']
    
    X_namesCat = ['MainActivity','Conditions']
   
    # The columns not to smooth
    toSmooth = [col for col in df.columns if col not in (Y_names or X_namesCat)]
  
    # Loop trhough each day and apply EWMA treating each day individually
    # Append the smoothed values in the helper dataframe dfEWMA
    for g in df.groupby([df.index.get_level_values('timestamp').year,
                         df.index.get_level_values('timestamp').month,
                        df.index.get_level_values('timestamp').day]):
        dfEWMA = dfEWMA.append(pd.ewma(g[1],span=span))  
    # Order the loop
    dfEWMA.sort_index(inplace=True)
    
    # Fill the null values with 0
    dfEWMA.fillna(0,inplace=True)
    
    df[toSmooth] = dfEWMA[toSmooth]

    #Remove the cold start instances! i.e. when the instances Rescue Time data
    # all sums up to 0
    df = df[(df[toSmooth].T!=0).any()]
    
    if ignoreCategorical:
        df =  df[[col for col in df.columns if col not in X_namesCat]]
    
    return df
"""
try to edit, didn't work       
def VARprocess(df,log=False):
    # Log transformation, relative difference and drop NULL values
    if (log):   
        df_log = np.log2(df+0.1).diff().dropna()
    # Vector Autoregression Process generation     
    maxAttr = len(df.columns) 
    # Find the right lag order
    orderFound = False
    while orderFound!=True:   
        try:
            model = VAR(df_log.ix[:,0:maxAttr])
            order = model.select_order() 
            orderFound = True
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            if str(exc_obj)=="data already contains a constant.":
                maxAttr = maxAttr - 1
            else:
                print str(exc_obj)
                maxAttr = int(str(exc_obj).split("-th")[0])-1
            print "Exception, reducing to n_attributes ",maxAttr
            orderFound = False
 
    n_lags = max(order.iteritems(), key=operator.itemgetter(1))[1]
    method = max(order.iteritems(), key=operator.itemgetter(1))[0]
    #print "n_lags ",n_lags
    #print "method ",method    
    results = model.fit(maxlags=n_lags, ic=method)
    return results
 
def VARforecast(df,results,window,log=False):
    lag_order = results.k_ar
    #lag_order = 2
    if (log):   
        df_log = np.log2(df+0.1).diff().dropna()
    else:
        df_log = df
    # Generate n prediction, where n is the window size, return array
    forecasts = results.forecast(df_log.values[-lag_order:], window)
    # Create the new index for the predictions
    ixPred = pd.date_range(df_log[-1:].index.to_pydatetime()[0]
        .strftime("%Y-%m-%d %H:%M:%S"),periods=window+1,freq='5min')
    ixPred = ixPred[-window:] #delete the first which exists
    # Generate a dataframe
    dfForecasts = pd.DataFrame(forecasts,index=ixPred,columns=df.columns.values)
    # Append the forecast to the original set, then add the header of the df
    # Invert the logarithmic scale and apply cumsum
    if (log): 
        df = df.ix[0:1,:].append(2**(df_log.append(dfForecasts))-0.1)
        dfReturn = pd.concat(2**df_log.append(dfForecasts))-0.1)
        #df.ix[0:1].concat(10**(df_log.append(dfForecasts))-0.1)
    else:
        dfReturn = df.append(dfForecasts)
    return dfReturn
    #try with this df.ix[:,14:]
    #df.ix[0:1,:].append(2**(df_log.append(dfForecasts))
"""

def VARprocess(df,log=False):
    # Log transformation, relative difference and drop NULL values
    if (log):    
        df = np.log(df+0.1).diff().dropna()
    # Vector Autoregression Process generation     
    maxAttr = len(df.columns) 
    # Find the right lag order
    orderFound = False
    while orderFound!=True:   
        try:
            model = VAR(df.ix[:,0:maxAttr])
            order = model.select_order() 
            orderFound = True
        except:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            if str(exc_obj)=="data already contains a constant.":
                maxAttr = maxAttr - 1
            else:
                maxAttr = int(str(exc_obj).split("-th")[0])-1
            print "Exception, reducing to n_attributes ",maxAttr
            orderFound = False
 
    n_lags = max(order.iteritems(), key=operator.itemgetter(1))[1]
    method = max(order.iteritems(), key=operator.itemgetter(1))[0]
    print "n_lags ",n_lags
    print "method ",method    
    results = model.fit(maxlags=n_lags, ic=method)
    return results
    
def VARforecast(df,results,window,log=False):
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
    if (log):     
        df = np.log(df+0.1).diff().dropna()
        dfReturn = (np.exp(pd.concat([df,
                                 df.append(dfForecasts)])).cumsum())-0.1
    else:
        dfReturn = df.append(dfForecasts)
    return dfReturn


def emailToId(df,col):
    df[col] = df[col].replace(to_replace=['mailto:maartjesean@gmail.com'],
                              value='arlearn7@gmail.com', regex=True)
    df[col] = df[col].replace(to_replace=['mailto:bibeglimbu@gmail.com'],
                              value='arlearn4@gmail.com', regex=True) 
    df = df[df[col].str.contains(r'arlearn')]
    df[col] = df[col].replace(to_replace=['mailto:arlearn','arlearn',
                            '@gmail.com'], value='', regex=True).astype(int) 
    return df
    
def nowFlow():
    # rounded minutes
    round_mins = (int(datetime.now().strftime('%M'))/5)*5
    timestamp = datetime.now().strftime('%Y-%m-%d %H:')+str(round_mins)
    df = pd.read_gbq("Select Flow FROM ["+globe.PRStable+"] WHERE timestamp='"+timestamp+"'", globe.PRSid)
    if df.empty:
        return -1
    else:
        return int(df.Flow[0])