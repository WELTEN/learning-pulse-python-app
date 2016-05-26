# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: activities.py
"""

import core
import globe
from core import *
from StringIO import StringIO
import requests

# -------------------
#/    ACTIVITIES    /
#-------------------

def df_activities(query):
    
    # Populating the dataframe
    time1 = time.time()
    ACframe = pd.read_gbq(query, globe.LRSid, private_key=globe.LRSkey)
    ACrsh = pd.DataFrame()
    CArsh = pd.DataFrame()
    if len(ACframe)>0:
        gdoc = requests.get(globe.googleDocCategories)
        data = gdoc.content
        GDdf = pd.read_csv(StringIO(data), error_bad_lines=False)
        n_app = len(GDdf)
        df = GDdf.stack()
        dict_apps = dict()
        for i in range(0,n_app):
            if len(df[i][df[i]=='x'])>0:
                dict_apps[df[i][0]] = df[i][df[i]=='x'].index.get_values()[0]
        ACframe['origin'] = ACframe['origin'].astype(str)
        ACdf = ACframe[['timestamp','objectId','resultDuration','actorId']]
        ACdf = core.emailToId(ACdf,'actorId')        
        #Rename columns
        ACdf.rename(columns={'objectId':'App'}, inplace=True)  
        ACdf['Cat'] = ACdf['App'].map(dict_apps)
    
        ACrsh = ACdf.groupby(['timestamp', 'actorId', 'App'])['resultDuration'].sum().unstack()
        CArsh = ACdf.groupby(['timestamp', 'actorId', 'Cat'])['resultDuration'].sum().unstack()
        ACrsh = ACrsh.fillna(0)
        CArsh = CArsh.fillna(0)
        #check distributon
        #df[df['objectId'].str.contains("MS Word")].ix[:,2:].notnull().stack().idxmax()[1]
        #CArsh.sum().plot(kind='bar')
    
        #dfAC,dfCA = activities.df_activities("SELECT *  FROM [xAPIStatements.xapiTableNew] WHERE origin = 'rescuetime' AND timestamp > PARSE_UTC_USEC('2015-11-23 07:00:00')  AND timestamp <  PARSE_UTC_USEC('2015-12-09 20:00:00') ORDER by timestamp")
        time2 = time.time()  
        print '4 ----- Activities processed in %0.1f s' % ((time2-time1))
    else:
        time2 = time.time()  
        print '4 ----- No activities found in this time window'
        
    return ACrsh,CArsh