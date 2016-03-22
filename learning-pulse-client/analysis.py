
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
from datetime import datetime, timedelta

#from google.appengine.ext import db

project_id = "768792801399"

#Date boundaries today
today = datetime.utcnow().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(1)).strftime('%Y-%m-%d')
today = yesterday
for i in range(7,8):
    
    print "Analysis for <arlearn"+str(i)+"@gmail.com> "+today
    
    # HEART-RATE
    #------------
    HRquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "objectID = 'HeartRate' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"

    HRframe = pd.read_gbq(HRquery, project_id) # Populating the dataframe
    HRdf = HRframe[['timestamp','result']] # Filtering the results  
    HRreshaped = HRdf.set_index(['timestamp']) #timestamp as index
    HRreshaped.rename(columns={'result':'Heart-rate'}, inplace=True)
    HRplot = HRreshaped.plot(color='r')
    #HRrm = pd.rolling_mean(HRreshaped, 200) #rolling mean in case needed
    #HRrm.plot(ax=HRplot, lw=2, label='HR average', color='g')
    
    HRdiscrete = HRreshaped.groupby(pd.TimeGrouper('5Min'))['Heart-rate'].mean()
    HRdiscrete.plot(label='5min mean', color='b') #add discrete mean
   
    
    # STEP COUNT
    #------------
    SCquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "objectID = 'StepCount' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"
    
    SCframe = pd.read_gbq(SCquery, project_id) # Populating the dataframe
    SCdf = SCframe[['timestamp','result']]  # Filtering the results 
    SCreshaped = SCdf.set_index(['timestamp']) #timestamp as index
    SCreshaped.rename(columns={'result':'Step-count'}, inplace=True) #Rename columns
    #SCrm = pd.rolling_mean(SCreshaped, 200)
    #SCplot = SCreshaped.plot(color='r')
    SCdiscrete = SCreshaped.groupby(pd.TimeGrouper('5Min'))['Step-count'].sum()
    #SCdiscrete.plot(label='5min mean', color='b')

    # RATINGS
    #------------
    RTquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "origin = 'rating' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"
    RTframe = pd.read_gbq(RTquery, project_id) # Populating the dataframe 
    RTdf = RTframe[['timestamp','objectId','result','lat','lng']]   # Filtering the results  
    #@todo understand how to save lat and lng when unstacking
    RTdf.rename(columns={'objectId':'Indicators'}, inplace=True) #Rename columns
    RTreshaped = RTdf.set_index(['timestamp','Indicators'])['result'].unstack()  
    RTplot = RTreshaped.plot(kind='area', stacked=False)    
    RTdiscrete =  RTreshaped
    
    
    # ACTIVITIES
    #------------
    ACquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "origin = 'rescuetime' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"
    ACframe = pd.read_gbq(ACquery, project_id) # Populating the dataframe 
    ACdf = ACframe[['timestamp','objectId','result']]
    ACdf.rename(columns={'objectId':'Applications'}, inplace=True)  
    #@todo remove duplicates by summing and not by taking the first
    ACreshaped = ACdf.set_index(['timestamp','Applications']) 
    ACreshaped = ACreshaped.drop(ACreshaped.index.get_duplicates())['result'].unstack()  
    ACdiscrete = ACreshaped.replace([0],[True]).fillna(False)
    
    final = pd.concat([HRdiscrete, SCdiscrete,RTdiscrete,ACdiscrete], axis=1)
    final = final.fillna(method='bfill') #Fill missing values 
    titlecsv = "arlearn"+str(i)+"@gmail.com_"+today    
    final.to_csv(titlecsv+".csv")
    #RTdiscrete = RTreshaped.groupby(pd.TimeGrouper('5Min'))['Step-count'].sum()
