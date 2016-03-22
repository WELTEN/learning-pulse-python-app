# -*- coding: utf-8 -*-
"""
Created on Tue Nov 10 10:52:17 2015

@author: ddm
"""

import urllib2
import json

joke =  urllib2.urlopen('http://tambal.azurewebsites.net/joke/random')
wjson = joke.read()
wjdata = json.loads(wjson)
print wjdata['joke']