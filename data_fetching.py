
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

#from google.appengine.ext import db

project_id = "768792801399"

#Date boundaries today
today = datetime.utcnow().strftime('%Y-%m-%d')
for i in range(7,8):
   
    # Heart-Rate querying
    HRquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "objectID = 'HeartRate' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"
    # Populating the dataframe
    HRframe = pd.read_gbq(HRquery, project_id)
    # Filtering the results 
    HRdf = HRframe[['timestamp','result']]
    n_HR = np.shape(HRframe)[0]
    label = "Heart-rate"
    title = "Heart-Rate <arlearn"+str(i)+"@gmail.com> "+today+" ("+ str(n_HR)+" entries)"
    #if n_HR>0:
        #HRdf.plot(x='timestamp',y='result',label=label,title=title) #single plot
   
    
    # Step-count querying
    SCquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "objectID = 'StepCount' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"
    # Populating the dataframe
    SCframe = pd.read_gbq(SCquery, project_id)
    # Filtering the results 
    SCdf = SCframe[['timestamp','result']]
    n_SC = np.shape(SCframe)[0]
    label = "Step count"
    title = "Step count arlearn"+str(i)+" "+today+" ("+ str(n_SC)+" entries)"
    #if n_SC>0:
        #SCdf.plot(x='timestamp',y='result',label=label,title=title)
    
    # Rating querying
    RTquery = "SELECT *  FROM [xAPIStatements.xapiTable] WHERE " \
    "origin = 'rating' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+today+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+today+" 20:00:00') ORDER by timestamp"
    RTframe = pd.read_gbq(RTquery, project_id)  
    RTdf = RTframe[['timestamp','objectId','result']]     
    RTreshaped = RTdf.set_index(['timestamp', 'objectId'])['result'].unstack()
    HRreshaped = HRdf.set_index(['timestamp'])
    concat = pd.merge(RTreshaped, HRreshaped)
    print concat
    #ax = concat.iloc[:,:4].plot(kind='bar')
    #concat.iloc[:,3:].plot(ax=ax)    
    #HRplot = HRreshaped.plot()
    #RTplot = RTreshaped.plot(kind='bar')
    #for ax, (colname, values) in zip(HRplot.flat, RTreshaped.iteritems()):
        #values.plot(ax=ax)
        
    """
    if (n_SC>0 and n_HR>0):  
        title = "Plot arlearn"+str(i)+" "+today+" |HR|="+ str(n_HR)+",|SC|="+ str(n_SC)
        HRmean = HRdf.mean()['result']     
        SCmean = SCdf.mean()['result'] 
        fitbitplot = HRdf.plot(x='timestamp',y='result',label="Heart-rate",
                               title=title,ax=RTplot) 
        HRplot = HRdf.plot(x='timestamp',y='result',label="Heart-rate") 
        #fitbitplot = SCdf.plot(x='timestamp',y='result',label="Step count",
        #          title=title,ax=ax)
        fitbitplot.axhline(HRmean,color='b')
        #fitbitplot.axhline(SCmean, color='g')
    else:
        print "Data not found for arlearn"+str(i)
    """