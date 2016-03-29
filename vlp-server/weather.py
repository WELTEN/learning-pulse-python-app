# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: weather.py
"""
from core import *

# --------------------
#/    WEATHER        /
#--------------------

def df_weather(filepath):
    # read CSV file stored in filepath    
    wdata = pd.read_csv(filepath,index_col=13,parse_dates=True)
    # select the relevant features    
    WDdf = wdata[['TemperatureC','Humidity','Sea Level PressurehPa',
                 'Conditions']]
    # add UTC+1 offset
    WDdf.index = WDdf.index + pd.DateOffset(hours=1)
    # rename columns inplace
    WDdf.rename(columns={'DateUTC':'Date','TemperatureC':'Temp','Sea Level PressurehPa':
    'Pressure'}, inplace=True)
    # store the legend of conditions indexes
    condLegend =  WDdf['Conditions'] #save legend of the weather conditions
    # transform conditions into categories code
    WDdf['Conditions'] = WDdf['Conditions'].astype('category').cat.codes
    
    return WDdf
