# -*- coding: utf-8 -*-
"""
@author: Daniele Di Mitri ddm@ou.nl
@title: core.py
"""
# system libraries
import numpy as np
import pandas as pd
import time
from datetime import datetime
from datetime import timedelta
import operator
import sys
import os
import urllib2
import json
import warnings
import requests
import smtplib
import pickle
import traceback


# app libraries
import globe
import ratings
import steps
import heartrate
import activities
import weather
import cube

# statistical libraries
from statsmodels.tsa.api import VAR
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pandas.io import gbq


#  CORE FUNCTIONS
def fetchData(start_date,end_date):
    """
    Description: this function is responsible to the 
    Input: the datetime to query the db
    Output: the datetime 
    """
    
    # Ratings
    query = "SELECT timestamp, actorId, objectId, resultResponse FROM "+globe.LRStable+" WHERE origin = 'rating' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfRT = ratings.df_ratings(query)
    
    # Steps
    query = "SELECT timestamp, actorId, resultResponse  FROM "+globe.LRStable+" WHERE objectID = 'StepCount' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfSC = steps.df_steps(query)
    
    # Heart Rate
    query = "SELECT timestamp, actorId, resultResponse  FROM "+globe.LRStable+" WHERE objectID = 'HeartRate' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfHR = heartrate.df_heartrate(query) 
    
    # Activities
    query = "SELECT timestamp, actorId, resultResponse, objectId, origin, " \
        " resultDuration FROM "+globe.LRStable+" WHERE origin = 'rescuetime' " \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"')  AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfAC,dfCA = activities.df_activities(query)
    
    # Weather
    query = "SELECT *  FROM "+globe.weather_table+" WHERE " \
        " date > PARSE_UTC_USEC('"+start_date+"')  AND date < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by date"
    dfWT = weather.df_weather(query,start_date,end_date)
    
    # --------------------
    #/    MERGE          /
    #--------------------  
    DF = pd.DataFrame()
    
    # Ratings - facultative
    if len(dfRT)>0:        
        DF =  dfRT.dropna()
        
    # Step counts - not really facultative
    if len(dfSC)>0:
        if len(DF)>0:
            DF = DF.join(dfSC).fillna(0) 
        else:
            DF = dfSC.to_frame()
            DF['timeframe'] =  DF.index.get_level_values(0).hour
    
    # Weather  - mandatory
    if len(dfWT)>0 and len(DF)>0: 
        DF = DF.join(dfWT).fillna(0)
    else:
        DF = pd.DataFrame()
        
    # Heartrate - mandatory
    if len(dfHR)>0 and len(DF)>0:     
        DF = DF.join(dfHR).dropna() 
    else:
        DF = pd.DataFrame()
        
    # Join the Categories 
    if len(dfCA)>0 and len(DF)>0:
        DF = DF.join(dfCA,how='left').fillna(0)  

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

def VARprocess(df,log=False):
    """
    Description: This function applies Vector Auto Regression
    Input: dataframe
    Output: VARresults object
    """  
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
            #if str(exc_obj)=="data already contains a constant.":
            maxAttr = maxAttr - 1
            #else:
            #maxAttr = int(str(exc_obj).split("-th")[0])-1
            #print "Exception, reducing to n_attributes ",maxAttr
            orderFound = False
 
    n_lags = max(order.iteritems(), key=operator.itemgetter(1))[1]
    method = max(order.iteritems(), key=operator.itemgetter(1))[0]
    #print "'----- n_lags ",n_lags
    #print "'----- method ",method    
    results = model.fit(maxlags=n_lags, ic=method)
    return results
    
def VARforecast(df,results,window,log=False):
    """
    Description: this function produces the forecasts of the var process
    Input: dataframe, VAR results, windows
    Output: forecasts
    """  
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
        dfReturn = dfForecasts
    return dfReturn

def emailToId(df,col):
    """
    Input: dataframe, column name of the actor id
    Output: dataframe with renamed actor ids
    """
    rindex = df[col].str.contains("mailto:maartjesean@gmail.com")    
    df.loc[rindex, col] = 'mailto:arlearn7@gmail.com'
    rindex = df[col].str.contains("mailto:bibeglimbu@gmail.com")    
    df.loc[rindex, col] = 'mailto:arlearn4@gmail.com'
    #df[col] = df[col].str.replace('mailto:bibeglimbu@gmail.com' , 'mailto:arlearn4@gmail.com')
    df = df[df[col].str.contains(r'arlearn')]
    rindex = df[col].str.contains('mailto:arlearn')
    df.loc[rindex, col] = df.loc[rindex, col].str.replace('mailto:arlearn' , '')
    rindex = df[col].str.contains('arlearn')
    df.loc[rindex, col] = df.loc[rindex, col].str.replace('arlearn' , '')
    rindex = df[col].str.contains('@gmail.com')
    df.loc[rindex, col] = df.loc[rindex, col].str.replace('@gmail.com' , '').astype(int)
    
    #df[col] = df[col].str.replace('mailto:arlearn' , '')
    #df[col] = df[col].str.replace('arlearn' , '')
    #df[col] = df[col].str.replace('@gmail.com' , '')
    #df[col] = df[col].astype(int) 
    return df
   
def flowPoints(c): 
    """
    Input: dataframe with Abilities and Challenge as columns
    Output: flow calculated
    """  
    n = 100-abs(c['Abilities']-c['Challenge'])
    d = float(c['Abilities']+c['Challenge'])/2
    return int(n*d/100)
    
def OWA_statement_Download(df):
    """
    Description: this function downloads the current weather 
    statement from Open Wheater Map. This function is mapped
    for each user depending their last coordinate
    Input: the dataframe
    Output: the json string
    Dependencies: datetime, urllib2, json
    """
    owa_lat = df.lat
    owa_lon = df.lng
        
    # Open the URL with urllib2
    page =  urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?lat='
            + str(owa_lat) +'&lon=' + str(owa_lon) + '&APPID=' + globe.owa_key)
    wjson = page.read()
    return str(json.loads(wjson))   
  
def WeatherDownload():
    """
    Description: this function fetches the last coordinates for each user
    from the BigQuery, thus it downloads the OWA statement for each one of them
    and saves everything in a CSV file (bad approach)
    Input: nothing
    Output: nothing
    Dependencies: pd,os
    """
    query = "SELECT last(lat) as lat,last(lng) as lng, actorId, last(timestamp)" \
    "as timestamp FROM (SELECT lat,lng,actorId,timestamp FROM [xAPIStatements.xapiTableNew]" \
    "WHERE origin = 'rating'  ORDER by timestamp) GROUP BY actorId"
   
    df = pd.read_gbq(query, globe.LRSid, private_key=globe.LRSkey)
    df = emailToId(df,'actorId')
    df = df.sort_values(by='timestamp').drop_duplicates(subset='actorId',keep='last')

    rindex = (datetime.today() - df.timestamp)> timedelta(hours=12)
    df.loc[rindex,'lat'] = globe.lat_default
    df.loc[rindex,'lng'] = globe.lng_default
    df['weather'] = df.apply(OWA_statement_Download, axis=1)
    df.timestamp = datetime.today()
    if os.path.exists(globe.weatherFile):
        # check if data for this tiframe has been downloaded yet
        dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')        
        df_read = pd.read_csv(globe.weatherFile, parse_dates=['timestamp'], date_parser=dateparse)        
        df_read = df_read.drop_duplicates(subset='actorId',keep='last')
        to_update = df_read[(datetime.today() - df_read.timestamp) > 
                    timedelta(minutes=5)].actorId.values
        df = df.loc[df['actorId'].isin(to_update)]
        if len(df)>0:
            with open(globe.weatherFile, 'a') as f:
               df.to_csv(f, header=None, index=False)
    else: # if file doesn't exist
        file(globe.weatherFile, 'w').close()
        with open(globe.weatherFile, 'a') as f:
           df.to_csv(f, header=True, index=False)
       
    print "----- Weather file updated in the CSV file"  
    
def processData(df_original,reg_mlme=True):
    """
    Description: core processing of the data. It's divided in two main steps:
    step 1, apply VAR to the fixed effects wrt to each actor, step 2, apply LMEM
    to whole dataset and learn 5 different models for each of the labels 
    Input: dataframe transformed with the whole history
    Output: dataframe with the forecast for each participant.
    """
    df_flat = df_original.reset_index()
    # Actors definition
    #count participants anre remove 10
    actors = df_flat.actorId.unique().tolist()
    if 10 in actors: actors.remove(10) # remove user no.10 (insufficient info)
    
    # Attributes definition
    #categoricals = ['MainActivity','lat','lng','weatherId'] 
    activities = list(df_original.ix[:,19:].columns.values)
    random_effects = activities + ['Steps']
    fixed_effects =  ['pressure', 'temp', 'humidity', 'hr_min', 'hr_avc', 'hr_mean',
                      'hr_std', 'hr_max', 'timeframe']
    labels = ['Abilities', 'Challenge', 'Productivity', 'Stress', 'Flow']
    
    # Dataframe to remember min e max for each user
    target_min = pd.DataFrame(np.nan, index=actors, columns=labels)
    target_max = pd.DataFrame(np.nan, index=actors, columns=labels)
    target_mean = pd.DataFrame(np.nan, index=actors, columns=labels)
    target_std = pd.DataFrame(np.nan, index=actors, columns=labels)
    
    # STEP 1) VAR on fixed effects 
    #-------------------------------
    window = 5  # Windows to predict
    df_future = pd.DataFrame() #prepare the future dataframe
    var_attributes = [item for item in fixed_effects if item not in ['timeframe']]
    for user in actors:    
        df_user = df_original.xs(user,level='actorId')
        df = df_user[var_attributes]     
        VARres = VARprocess(df)    
        forecasts = VARforecast(df,VARres,window)        
        #plt = forecasts.plot() # prediction plot
        #plt.axvline(forecasts.index[-window])  
        forecasts['actorId'] = user
        forecasts['timeframe'] = forecasts.index.hour                      
        df_future = df_future.append(forecasts)  
        # offtopic, add max and min
        for target in (labels):   
            target_min[target][user] = min(df_user[target])
            target_max[target][user] = max(df_user[target])
            target_mean[target][user] = df_user[target].mean()
            target_std[target][user] = df_user[target].std()
    # add intercept term
    df_future['Intercept'] = 1
    df_future = df_future.reset_index().set_index(['index','actorId']).sort_index()
    # ------------------------------- end VAR
        
    # STEP 2) Linear Mixed Effect Model
    # ------------------------------- 
    data = df_flat
    data['intercept'] = 1 # set the intercept term
    LMEM_models = [] # create a list of models, for multi output
    exog = data[fixed_effects + ['intercept']] # the attributes from which to predict
    exog_re = data[random_effects] # random effects
    groups = data['actorId'] # group definition
    
    # Training phase of four model, one per each label
    for target in labels:
        endog = data[target] # endogenous, ie the values we want to predict
        if ((reg_mlme==False) 
            and os.path.exists('model_'+target+'.pickle')):
            LMEM_results = pickle.load(open('model_'+target+'.pickle', 'rb'))
            LMEM_models.append(LMEM_results)
        else:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore")
                LMEM_model = sm.MixedLM(endog, exog, groups=groups, exog_re=exog_re)
                LMEM_results = LMEM_model.fit()
                LMEM_results.save('model_'+target+'.pickle',remove_data=False)
                LMEM_models.append(LMEM_results)
        
    # Coefficients importance averaging
    coeff = pd.DataFrame(index=range(0,len(exog.T)),data={'coefficients':0.0}, dtype='float').coefficients
    for i in range(0,len(coeff)):
        for j in range(0,len(LMEM_models)):
            coeff[i] = coeff[i]+LMEM_models[j].fe_params[i]
    coeff = coeff/len(LMEM_models)
    
    # Test phase for each of the four models
    df = df_future.reset_index()   
    exog = df[fixed_effects]
    exog['intercept'] = 1
    for i in range(0,len(labels)):
        t = labels[i]
        df[t] = LMEM_models[i].predict(exog)
        # normalization
        for u in actors:
            actual = df[df['actorId']==u][t]
            rindex = df[df['actorId']==u][t].index
            # Normalization (x_max-x_min)*(x_i/100)+x_min
            df.loc[rindex,t] = (target_max[t][u] - target_min[t][u])*(actual/
            100)+target_min[t][u]
        df[t] = df[t].astype('int')    
    df = df.rename(columns={'index':'timestamp'})
    return df

def cubeUpdates():
    df = currentFlows()
    d = globe.cubeUsersMapping
    if len(df)>0:
        for key, value in d.iteritems():
            if len(df[df.actorId==value].Flow)>0:
                cube.updateCube(key,int(df[df.actorId==2].Flow.values))
                print "---- Updated Cube: "+key+", ActorId: "+ str(value)  


def currentFlows():
    """
    Input: none
    Output: current Flow for each actorId
    """  
    # rounded minutes
    round_mins = (int(datetime.now().strftime('%M'))/5)*5
    if round_mins<10:
        round_mins = str(round_mins).zfill(2)
    else:
        round_mins = str(round_mins)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:')+round_mins
    df = pd.read_gbq("Select actorId,Flow FROM ["+globe.PRSforecast+"] WHERE timestamp='"+timestamp+"'",
                     globe.PRSid, private_key=globe.PRSkey)
    return df