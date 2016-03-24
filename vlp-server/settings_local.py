"""
Created on Mon Mar 21 14:45:37 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: settings_local.py
"""
#  IMPORTS
#**************************

from __future__ import division
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import entropy
from scipy import signal
import statsmodels.api as sm
import ConfigParser

#  GLOBAL VARIABLES
#**************************

# Get configuration file
configParser = ConfigParser.RawConfigParser()
configFilePath = r'/Users/daniele/Documents/VisualLearningPulse/code/settings.config'
configParser.read(configFilePath)

# Learning Record store id
LRSid = configParser.get('vlp', 'lrs_id')
# LRS tablename
LRStable = configParser.get('vlp', 'lrs_table')
# Prediction Record store id
PRSid = configParser.get('vlp', 'prs_id')
# LRS tablename
LRStable = configParser.get('vlp', 'prs_table')


#Date boundaries today
today = datetime.utcnow().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(1)).strftime('%Y-%m-%d')

start_first_experiment = '2015-11-23 07:00:00'
end_first_experiment = '2015-12-09 20:00:00'
