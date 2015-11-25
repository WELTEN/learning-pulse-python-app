# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 12:04:05 2015

@author: ddm
"""
import openweather
from datetime import datetime

# create client
ow = openweather.OpenWeather()

print ow.get_weather(4885)