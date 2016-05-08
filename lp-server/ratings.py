# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: ratings.py
"""
from core import *

# --------------------
#/    RATINGS        /
#--------------------
    
def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x'], point['y'], str(point['val']))
        
# Function to label the Flow points with corresponding values
def FPSscore(c):
    fp1 = float((100-c['Stress'])+c['Productivity'])/2
    return int((fp1+c['Flow'])/2)
    
# Function to label the Flow points with corresponding values
def flowPoints(c): 
    n = 100-abs(c['Abilities']-c['Challenge'])
    d = float(c['Abilities']+c['Challenge'])/2
    return int(n*d/100)


def df_ratings(query): 
    time1 = time.time()
    # Populating the dataframe 
    RTframe = pd.read_gbq(query, globe.LRSid) 
    # Filtering the results
    RTdf = RTframe[['timestamp','objectId','resultResponse','lat','lng']]
    #Rename the columns
    RTdf.rename(columns={'objectId':'Indicators'}, inplace=True)
    RTdf.rename(columns={'resultResponse':'value'}, inplace=True)    
    #Reshape the DataFrame
    RTrsh = RTdf.set_index(['timestamp','Indicators'])['value']
    # In case of duplicates     
    RTrsh = RTrsh.drop(RTrsh.index.get_duplicates())
    RTrsh = RTrsh.unstack() 
    
    # Fix: the index will shift -1 hr. E.g. 9:00 -> 8:00 
    # Indicating the rating done at 9:00 for the 8:xx activities    
    RTrsh.index = RTrsh.index-pd.offsets.Hour(1)
    
    # Activity Category
    #@todo mapping main activity
    actLegend = RTrsh['MainActivity']
    RTrsh['MainActivity'] = RTrsh['MainActivity'].astype('category').cat.codes
    
    # 1. First check for missing values and fill them backward
    # 2. Then check again and fill them forward (workaround for latest missing)
    # 3. Then cast to int
    RTrsh = RTrsh.fillna(method='bfill').fillna(method='pad').astype(int) 
        
    # Calculate the Flow-Score - see function flowPoints for explaination   
    RTrsh['Flow'] = RTrsh.apply(flowPoints, axis=1)
    
    # The correlation between Flow and Productivity 
    #flowProdCorr = RTrsh[['Productivity','Flow']].corr().iloc[0]['Flow']
    time2 = time.time()  
    print 'Ratings values read from BigQuery in %0.3f s' % ((time2-time1))
    
    return RTrsh
