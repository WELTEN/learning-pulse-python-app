# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: activities.py
"""

from core import *
from StringIO import StringIO
import requests

# -------------------
#/    ACTIVITIES    /
#-------------------

def df_activities(query):
    
    # Populating the dataframe
    time1 = time.time()
    ACframe = pd.read_gbq(query, globe.LRSid)
    # Filtering the results 
    ACframe['origin'] = ACframe['origin'].astype(str)
    ACdf = ACframe[['timestamp','objectId','resultDuration']]
    
    ACdf.rename(columns={'objectId':'App'}, inplace=True)  

    # Grouping steps by sum
    ACrsh = ACdf.groupby(['timestamp', 'App'])['resultDuration'].sum().unstack()
    # Fill null values
    ACrsh = ACrsh.fillna(0)
    ACrsh = ACrsh[ACrsh.sum().sort_values(ascending=False).index.tolist()]
    ACrsh = ACrsh.loc[:,ACrsh.var()>10]         
    
    #Mapping
    gdoc = requests.get('https://docs.google.com/spreadsheets/d/183WssCz8deRJkx8ITadM9HtK9Z4W5kWufmPNN-wqYcQ/export?format=csv&id')
    data = gdoc.content
    GDdf = pd.read_csv(StringIO(data), error_bad_lines=False)
    n_app = len(GDdf)
    df = GDdf.stack()
    dict_apps = dict()
    for i in range(0,n_app):
        if len(df[i][df[i]=='x'])>0:
            dict_apps[df[i][0]] = df[i][df[i]=='x'].index.get_values()[0]
    #df[df['objectId'].str.contains("MS Word")].ix[:,2:].notnull().stack().idxmax()[1]
    ACdf['Cat'] = ACdf['App'].map(dict_apps)
    CArsh = ACdf.groupby(['timestamp', 'Cat'])['resultDuration'].sum().unstack()
    #CArsh.sum().plot(kind='bar')
    time2 = time.time()  
    print 'Activity processed in %0.1f s' % ((time2-time1))
    #check distributon
    #dfAC,dfCA = activities.df_activities("SELECT *  FROM [xAPIStatements.xapiTableNew] WHERE origin = 'rescuetime' AND timestamp > PARSE_UTC_USEC('2015-11-23 07:00:00')  AND timestamp <  PARSE_UTC_USEC('2015-12-09 20:00:00') ORDER by timestamp")

    return ACrsh,CArsh