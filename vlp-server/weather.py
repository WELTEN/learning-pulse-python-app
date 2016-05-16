# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: weather.py
"""
import core
import globe
from core import *
import json
# --------------------
#/    WEATHER        /
#--------------------

def jsonToDF(string):
    obj = json.loads(string)
    
    if 'coord' in obj:
        lat = float(obj['coord']['lat'])
        lng = float(obj['coord']['lon'])
    else:
        lat = globe.lat_default
        lng = globe.lng_default
    if 'weather' in obj:
        weatherId = int(obj['weather'][0]['id'])
    else:
        weatherId = 0
    if 'main' in obj:
        pressure = float(obj['main']['pressure'])/100
        temp = float(obj['main']['temp'])-273.15 
        humidity = float(obj['main']['humidity'])
    else:
        # default values
        pressure = 10.13
        temp = 9.75 
        humidity = 68
        
    return lat,lng,weatherId,pressure,temp,humidity
    

def df_weather(query,start_date,end_date):        
    # Populating the dataframe
    time1 = time.time()
    if os.path.exists(globe.weatherFile):
        dateparse = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f')
        WTdf = pd.read_csv(globe.weatherFile, parse_dates=['timestamp'], date_parser=dateparse)
        mask = (WTdf['timestamp'] > start_date) & (WTdf['timestamp'] <= end_date)
        WTdf = WTdf.loc[mask]
        if len(WTdf)>0:
            WTdf['weather'] = WTdf['weather'].replace({"u'":"'","'":'"'}, regex=True)
            WTdf['lat'], WTdf['lng'], WTdf['weatherId'], WTdf['pressure'],\
            WTdf['temp'], WTdf['humidity'] = zip(*WTdf['weather'].map(jsonToDF))
            WTrsh = WTdf.drop(['weather'], axis=1)
            WTrsh.set_index(['timestamp','actorId'], inplace=True)
            WTrsh = WTrsh.unstack().resample('5min').fillna(method='bfill').fillna(method='pad').stack()
            time2 = time.time()
            print '----- Weather generation (from CSV) took %0.1f s' % ((time2-time1))
            return WTrsh
    WTframe = pd.read_gbq(query, globe.PRSid) 
    WTrsh = pd.DataFrame()
    if len(WTframe)>0:
        WTdf = WTframe[['date','status','user']] 
        WTrsh = core.emailToId(WTdf,'user')
        WTrsh['status'] = WTrsh['status'].replace({"u'":"'","'":'"'}, regex=True)
        WTrsh['lat'], WTrsh['lng'], WTrsh['weatherId'], WTrsh['pressure'],\
        WTrsh['temp'],WTrsh['humidity'] = zip(*WTrsh['status'].map(jsonToDF))
        WTrsh.rename(columns={'date':'timestamp'}, inplace=True)
        WTrsh.rename(columns={'user':'actorId'}, inplace=True)  
        WTrsh = WTrsh.drop(['status'], axis=1)
        WTrsh.set_index(['timestamp','actorId'], inplace=True)
        WTrsh = WTrsh.unstack().resample('5min').fillna(method='bfill').fillna(method='pad').stack()
        time2 = time.time()
        print '----- Weather generation (from BigQuery) took %0.1f s' % ((time2-time1))
    else:
        time2 = time.time()
        print '----- There is no weather data in this time-window'  
    return WTrsh
