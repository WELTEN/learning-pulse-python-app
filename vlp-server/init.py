# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: plots.py
"""
from settings_local import *

import ratings
import steps
import heartrate
import activities
import weather

def fetch_data(userid,start_date,end_date):

    actorID =  "'mailto:arlearn"+str(user_id)+"@gmail.com'"  
    
    # Ratings
    query = "SELECT *  FROM [xAPIStatements.xapiTableNew] WHERE " \
        "origin = 'rating' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfRT = ratings.df_ratings(query)
    
    # Steps
    query = "SELECT *  FROM [xAPIStatements.xapiTableNew] WHERE " \
        "objectID = 'StepCount' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfSC = steps.df_steps(query)
    
    # Heart Rate
    query = "SELECT *  FROM [xAPIStatements.xapiTableNew] WHERE " \
        "objectID = 'HeartRate' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"') AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfHR = heartrate.df_heartrate(query) 
    
    # Activities
    query = "SELECT *  FROM [xAPIStatements.xapiTableNew] WHERE " \
        "origin = 'rescuetime' AND actorID="+actorID+ \
        " AND timestamp > PARSE_UTC_USEC('"+start_date+"')  AND timestamp < " \
        " PARSE_UTC_USEC('"+end_date+"') ORDER by timestamp"
    dfAC = activities.df_activities(query)
    
    # Weather
    dfWT = weather.df_weather(query)
    
    
    
    