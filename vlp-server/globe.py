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
    global PRStable
    global start_first_experiment
    global end_first_experiment
    
    configParser = ConfigParser.RawConfigParser() # Get configuration file
    configFilePath = r'/Users/daniele/Documents/VisualLearningPulse/code/settings.config'
    configParser.read(configFilePath)
    
    LRSid = configParser.get('vlp', 'lrs_id') # Learning Record store id
    LRStable = configParser.get('vlp', 'lrs_table') # LRS tablename
    PRSid = configParser.get('vlp', 'prs_id') # Prediction Record store id
    PRStable = configParser.get('vlp', 'prs_table') # PRS tablename
    
    start_first_experiment = '2015-11-23 07:00:00'
    end_first_experiment = '2015-12-09 20:00:00'
    
    start_second_experiment = '2016-04-11 07:00:00'
    end_second_experiment = '2016-04-23 20:00:00'