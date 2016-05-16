# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: init.py
"""
from core import *
import globe
import plots

# Import global names
globe.setGlobalNames()

# BigQuery update
# ------------------------------- 
r = requests.get("http://learning-pulse.appspot.com/syncBigQuery")
print "----- SyncBigQuery responded with status: " + str(r.status_code)
r = requests.get("http://learning-pulse.appspot.com/importers")
print "----- Importers responded with status: " + str(r.status_code)

# Download weather
# ----------------
WeatherDownload()


# Data second experiment
regenerate = False
if regenerate: 
    # Fetch and transform User data from the Learning Record Store
    df_original = fetchData(globe.start_second_experiment,globe.end_second_experiment)
    df_original_flat = df_original.reset_index()
    gbq.to_gbq(df_original_flat,globe.PRShistory,globe.PRSid,if_exists='replace')
else:
    # download from BigQuery    
    df_original_flat =  pd.read_gbq("Select * FROM ["+globe.PRShistory+"]", globe.PRSid)
    df_original = df_original_flat.set_index(['timestamp','actorId']).sort_index()

# Fetch other data 
if os.path.exists('last_sync.txt'):
    f = open(filename)
    last_date = f.read()
else:
    last_date = '2016-05-13 08:00:00'
current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
df_new = fetchData(last_date,current_date)
df_appended = pd.concat([df_original,df_new])
df_forecast = process_data(df_appended)
gbq.to_gbq(df_forecast,globe.PRSforecast,globe.PRSid,if_exists='replace')

#update the last sync date
if os.path.exists('last_sync.txt'):
    file('last_sync.txt', 'w').close()
    with open('last_sync.txt', 'w') as f:
        f.write(current_date)
        
        
# ------------------------------- end LMEM

