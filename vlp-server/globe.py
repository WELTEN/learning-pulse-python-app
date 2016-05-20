#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 14:45:37 2016
@author: ddm@ou.nl
@title: globe.py
"""

import ConfigParser

#  GLOBAL VARIABLES
#**************************
LRSid = LRStable = PRSid = PRStable = ''

def setGlobalNames():
    global LRSid 
    global LRStable
    global PRSid 
    global PRSforecast
    global PRShistory
    global weather_table
    global start_first_experiment
    global end_first_experiment
    global start_second_experiment
    global end_second_experiment
    global lat_default
    global lng_default
    global owa_key
    global weatherFile
    global googleDocCategories
    global senderPassword
    global senderEmail
    global receiverEmail
    global LRSkey
    global PRSkey
    global cubeUsersMapping
    
    configParser = ConfigParser.RawConfigParser() # Get configuration file
    configFilePath = r'/Users/daniele/Documents/VisualLearningPulse/code/settings.config'
    configParser.read(configFilePath)
    
    # BigQuery ID of the LRS
    LRSkey = configParser.get('vlp', 'LRSkey')
    LRSid = configParser.get('vlp', 'lrs_id') # Learning Record store id
    # Main LRS Table    
    LRStable = configParser.get('vlp', 'lrs_table') # LRS tablename
    # Side Table for the Weather    
    weather_table = configParser.get('vlp', 'weather_table') # LRS tablename    
    
    PRSkey = configParser.get('vlp', 'PRSkey')
    PRSid = configParser.get('vlp', 'prs_id') # Prediction Record store id
    PRSforecast = configParser.get('vlp', 'prs_forecast') # PRS tablename
    PRShistory = configParser.get('vlp', 'prs_history') # PRS tablename
    
    senderEmail = configParser.get('vlp', 'senderEmail')
    senderPassword = configParser.get('vlp', 'senderPassword')
    receiverEmail = configParser.get('vlp', 'receiverEmail')
    
    start_first_experiment = '2015-11-23 07:00:00'
    end_first_experiment = '2015-12-09 20:00:00'
    
    start_second_experiment = '2016-04-12 14:00:00'
    end_second_experiment = '2016-04-29 18:00:00'
    
    lat_default = 50.877861
    lng_default = 5.958490
    
    weatherFile = r'/Users/daniele/Documents/VisualLearningPulse/code/weather.csv'
    owa_key = configParser.get('vlp', 'owa_key')
    
    googleDocCategories = 'https://docs.google.com/spreadsheets/d/183WssCz8deRJkx8ITadM9HtK9Z4W5kWufmPNN-wqYcQ/export?format=csv&id'
    
    cubeUsersMapping = {'A':3,'B':4,'C':5,'D':6}