# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 10:52:17 2015

@author: ddm
"""

import urllib2
import json

owa_key = "0d68f7a39b4bbc47ac1d14ffadcbe17a"
owa_lat = "50.877861"
owa_lon = "5.958490"

#here array of locations and then for loop

weather =  urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?lat='+owa_lat 
		   +'&lon=' + owa_lon + '&APPID=' + owa_key)
wjson = weather.read()
wjdata = json.loads(wjson)
print wjdata