# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: weather.py
"""
import core
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
        lat = 50.8779846 #globe.lat_default
        lng = 5.9582749 #globe.lng_default
    if 'weather' in obj:
        weatherId = int(obj['weather'][0]['id'])
    else:
        weatherId = 0
    if 'main' in obj:
        pressure = float(obj['main']['pressure'])/100
        temp = float(obj['main']['temp'])-273.15 
        humidity = float(obj['main']['humidity'])
    else:
        pressure = 10.13
        temp = 9.75 
        humidity = 68
    #windSpeed = float(obj['wind']['speed'])
    #windDeg = int(obj['wind']['deg'])
        
    return lat,lng,weatherId,pressure,temp,humidity
    

def df_weather(query):
        
    # Populating the dataframe
    time1 = time.time()
    WTframe = pd.read_gbq(query, globe.PRSid) 
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
    print 'Weather generation took %0.1f s' % ((time2-time1))
    return WTrsh
