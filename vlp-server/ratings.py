# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: ratings.py
"""
import core
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
    
def flowPoints1(col1,col2): 
    n = 100-abs(col1-c['Challenge'])
    d = float(c['Abilities']+c['Challenge'])/2
    return int(n*d/100)

def activityToId(col):
    #activities = {'reading': '1','writing':'2','meeting': '3', 
    #'communication': '4','other': '5'}
    #col = col.map(activities)
    return col.replace(to_replace=['reading','writing','meeting','communication','other'],
                              value=['1','2','3','4','5'], regex=True).astype(int)

def df_ratings(query): 
    time1 = time.time()
    # Populating the dataframe 
    RTframe = pd.read_gbq(query, globe.LRSid,private_key=globe.LRSkey)
    RTrsh = pd.DataFrame()
    if len(RTframe)>0:
        # Filtering the results 
        RTdf = RTframe[RTframe['objectId']!='dashboard']
        RTdf = RTdf[['timestamp','objectId','resultResponse','actorId']]
        
        #Rename the columns
        RTdf.rename(columns={'objectId':'Indicators'}, inplace=True)
        RTdf.rename(columns={'resultResponse':'value'}, inplace=True)
        
        #Drop the entries which are exactely identical
        RTdf = RTdf.drop_duplicates()
        
        #Drop the duplicate ratings (not indentical), take the last
        RTdf = RTdf.set_index(['timestamp','actorId','Indicators']).sort_index()
        RTdf = RTdf.groupby(level=RTdf.index.names).last().reset_index()
        
        RTrsh = RTdf.pivot_table(values='value',
                              index=['timestamp','actorId'],
                               columns=['Indicators'],aggfunc=lambda x: x.iloc[0])  

        RTrsh.reset_index(inplace=True)
        # Fix: the index will shift -1 hr. E.g. 9:00 -> 8:00 
        # Indicating the rating done at 9:00 for the 8:xx activities
        RTrsh.timestamp = RTrsh.timestamp - pd.offsets.Hour(1)
        # Retstrict to the arlearn value
        RTrsh = core.emailToId(RTrsh,'actorId')
        RTrsh['timeframe'] = RTrsh.timestamp.map(lambda x: x.strftime('%H')).astype(int)       
        RTrsh.set_index(['timestamp','actorId'], inplace=True)
        RTrsh = RTrsh.dropna()                
        
        RTrsh['MainActivity'] = activityToId(RTrsh['MainActivity'])
        
        # 1. First check for missing values and fill them backward
        # 2. Then check again and fill them forward (workaround for latest missing)
        # 3. Then cast to int
        RTrsh = RTrsh.fillna(method='bfill').fillna(method='pad').astype(int) 
            
        # Calculate the Flow-Score - see function flowPoints for explaination   
        RTrsh['Flow'] = RTrsh.apply(flowPoints, axis=1)
        
        #Create 5 minutes intervals
        RTrsh = RTrsh.unstack().fillna(-1).resample('5Min').fillna(method='pad').stack().replace(-1,np.NaN)
        
        # The correlation between Flow and Productivity 
        #flowProdCorr = RTrsh[['Productivity','Flow']].corr().iloc[0]['Flow']
        time2 = time.time()  
        print '----- Ratings values read from BigQuery in %0.3f s' % ((time2-time1))
    else:
        print '----- No ratings found in this time-window'
        
    return RTrsh
