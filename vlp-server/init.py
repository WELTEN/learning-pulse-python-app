#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: init.py
"""
from core import *
import globe
import plots

# Flags to regenerate historical data or 
regenerate_data = True
regenerate_mlme = False
store_mode = True

weekday = datetime.today().weekday()
curr_hour = datetime.today().hour
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

gt1 = time.time() 

# set the limit from Mon to Fri and from 8 to 18
if weekday < 5 and curr_hour > 7 and curr_hour < 19:
    print "+++++ START NEW CYCLE AT "+current_time+" +++++"
    try:
        # Import global names
        globe.setGlobalNames()
        
        # BigQuery update
        # ------------------------------- 
        r = requests.get("http://learning-pulse.appspot.com/syncBigQuery")
        print "0.1 ----- SyncBigQuery responded with status: " + str(r.status_code)
        r = requests.get("http://learning-pulse.appspot.com/importers")
        print "0.2 ----- Importers responded with status: " + str(r.status_code)
        
        # Download weather
        # ----------------
        WeatherDownload()           
        print "0.3 ----- Weather file updated in the CSV file"  

        current_date =  datetime.now().strftime('%Y-%m-%d %H:%M:%S')      
        if os.path.exists('last_sync.txt'):
            f = open('last_sync.txt')
            last_date = f.read()
        else:
            last_date = '2016-05-17 08:00:00'

        print "...... The last date is " + last_date    

        df_new = fetchData(last_date,current_date)
        if len(df_new)>0:
            
            # Regenerate Data second experiment
            if regenerate_data: 
                # Fetch and transform User data from the Learning Record Store
                print "6 ----- Regenerating data" 
                df_original = fetchData(globe.start_second_experiment,
                                        globe.end_second_experiment)
                df_original_flat = df_original.reset_index()
                gbq.to_gbq(df_original_flat,globe.PRShistory,globe.PRSid,
                           if_exists='replace',private_key=globe.PRSkey)
            else:
                # download from BigQuery    
                print "6 ----- Reading data from the BigQuery" 
                df_original_flat =  pd.read_gbq("Select * FROM ["+ \
                    globe.PRShistory+"]", globe.PRSid,private_key=globe.PRSkey)
                df_original = df_original_flat.set_index(['timestamp',
                'actorId']).sort_index()
            
            # STORE new Historical data
            df_history = pd.concat([df_original,df_new]).sort_index()
            df_history = df_history[~df_history.index
                .duplicated(keep='last')].fillna(0)
            if store_mode and len(df_history)>0:
                try:
                    gbq.to_gbq(df_history.reset_index(),globe.PRShistory,globe.PRSid,
                               if_exists='replace',private_key=globe.PRSkey)
                except:
                    gbq.to_gbq(df_history.reset_index(),globe.PRShistory,globe.PRSid,
                               if_exists='replace',private_key=globe.PRSkey)
            else:
                print "df_history vuoto at "+current_date


                
            # PROCESS new data
            print "7 ----- Starting the processing" 
            new_forecast = processData(df_new,reg_mlme=regenerate_mlme)

            
            print "8 ----- Storing forecasts" 
            # STORE new Forecasts data
            old_forecast =  pd.read_gbq("Select * FROM ["+ \
                    globe.PRSforecast+"]", globe.PRSid,private_key=globe.PRSkey)  
            df_forecast = pd.concat([old_forecast,new_forecast]).set_index(
            ['timestamp','actorId']).sort_index()
            df_forecast = df_forecast[~df_forecast.index
                .duplicated(keep='last')].reset_index()   
            
            if store_mode:
                gbq.to_gbq(df_forecast,globe.PRSforecast,globe.PRSid,
                           if_exists='replace',private_key=globe.PRSkey)
            
            print "+++++ Forecast recalculated +++++" 
            
            #update the last sync date
            delta = timedelta(hours=-2)
            last_date = datetime.now() + delta
            if not os.path.exists('last_sync.txt'):
                file('last_sync.txt', 'w').close()  
            if len(df_new)>0:
                with open('last_sync.txt', 'w') as f:
                    f.write(last_date.strftime('%Y-%m-%d %H:%M:%S')+'\n')     
        else:
            print "+++++ No new data +++++" 
            
        ###
        # Update the cubes
        # ----------------
        cubeUpdates()
        
        # Last execution
        # ----------------
        if not os.path.exists('last_exec.txt'):
            file('last_exec.txt', 'w').close()  
        with open('last_exec.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\n') 

    except Exception, err:
        msg  = str(traceback.format_exc())
        server = smtplib.SMTP('mail.gandi.net', 25)
        server.starttls()
        server.login(globe.senderEmail, globe.senderPassword)
        server.sendmail('VLP alert <'+globe.senderEmail+'>', globe.receiverEmail, msg)
        server.quit()

if not os.path.exists('last_activ.txt'):
    file('last_activ.txt', 'w').close()  
with open('last_activ.txt', 'w') as f:
    f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'\n')
    
gt2 = time.time() 
print 'END ----- Total script execution %0.1f m' % ((gt2-gt1)/60)