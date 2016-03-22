# -*- coding: utf-8 -*-
"""
Created on Thu Nov 26 10:16:59 2015
@author: Daniele Di Mitri ddm@ou.nl
@title: weather-download.py
"""

import urllib2

#import csv

year = '2015'
days = ['23/11','24/11','25/11','26/11','27/11','30/11','01/12','02/12','03/12',
        '04/12','07/12','08/12','09/12']
station = 'EHBK'
#page = "http://www.wunderground.com/weatherstation/WXDailyHistory.asp?
airport_page = "http://www.wunderground.com/history/airport/EHBK/"

csv_content = "TimeCET,TemperatureC,Dew PointC,Humidity,Sea Level PressurehPa," \
"VisibilityKm,Wind Direction,Wind SpeedKm/h,Gust SpeedKm/h,Precipitationmm," \
"Events,Conditions,WindDirDegrees,DateUTC\n"

for item in days:
    day,month = item.split('/')
    url = airport_page + year + "/" + month + "/" + day + "/" + \
    "DailyHistory.html?HideSpecis=1&theprefset=SHOWMETAR&theprefvalue=0&format=1"
    print url
    response = urllib2.urlopen(url)
    page_content = '\n'.join(response.read().split('\n')[2:]) 
    csv_content += page_content.replace('<br>', '').replace('<br />', '').replace('\n\n', '\n')
csv_title = "weather_data.csv" 
with open(csv_title, 'w') as f:
   f.write(csv_content)

