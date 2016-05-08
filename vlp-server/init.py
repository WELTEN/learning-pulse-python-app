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
  
regenerate = False

if regenerate: 
    # Fetch and transform User data from the Learning Record Store
    df_original = fetchData(globe.start_second_experiment,globe.end_second_experiment)
    df_original_flat = df_original.reset_index()
else:
    # download from BigQuery    
    df_original_flat =  pd.read_gbq("Select * FROM ["+globe.PRStable+"]", globe.PRSid)
    df_original = df_original_flat.set_index(['timestamp','actorId']).sort_index()

window = 5 # number of timeframe to predict
actors = df_original_flat.actorId.unique().tolist()

df_future = pd.DataFrame() 
for user in actors:
    df_pred = pd.DataFrame() 
    df = df_original.xs(user,level='actorId')
    #df = df[df.sum().sort_values(ascending=False).index.tolist()]
    #df = df.loc[:,df.sum()>250]
    
    #VAR process
    dt = df[['Abilities', 'Challenge', 'Productivity', 'Stress','Flow', 
             'pressure', 'temp', 'humidity','hr_min', 'hr_avc', 'hr_mean',
             'hr_std', 'hr_max']]    
    VARres = VARprocess(dt)    
    forecasts = VARforecast(dt,VARres,window)    
    
    #Forecast plots    
    plt = forecasts.ix[-30:,:].plot()
    plt.axvline(forecasts.index[-window])  
    
    # Prediction table
    df_pred = df.append(forecasts.ix[-window:])
    
    #Fill NaN strategy
    
    # timeframe
    df_pred['timeframe'] = np.where(df_pred['timeframe'] == np.NaN,
                                df_pred['timeframe'].index.hour,
                                df_pred['timeframe'].index.hour)
                                
    # weatherId, MainActivity (categoricals)
    categoricals = ['MainActivity','lat','lng','weatherId'] 
    df_pred[categoricals] = df_pred[categoricals].fillna(method='pad') 
    activities = list(df.ix[:,19:].columns.values)                      
    df_pred[activities] = df_pred[activities].fillna(method='pad') 
    #@todo smooth the activities use
    #np.linspace(1,0.5,window) 
    # steps 
    if df.ix[-1,19:].sum()>0:
        df_pred['Steps'] = df_pred['Steps'].fillna(0)
    else:
        df_pred['Steps'] = df_pred['Steps'].fillna(method='pad')
    df_future = df_future.append(df_pred)  

df_future = df_future.set_index(['timestamp','actorId']).sort_index()
df_future_flat = df_future.reset_index()   
    
# Mixed Model
#--------------------  
"""
endog = data['Flow']
data['Intercept'] = 1
exog = pd.concat([data['Intercept'],data.ix[:,13:20]],axis=1)
exog_re = data[['Steps','Browsing','Develop_Code']]
md = sm.MixedLM(endog, exog, groups=data['actorId'], exog_re=exog_re)
mdf = md.fit()
print(mdf.summary())
"""
"""
# Smooth values
df = smoothValues(df,True)
    
# VAR process 
#--------------------      
window = 5 # number of timeframe to predict
results = VARprocess(df)
forecasts = VARforecast(df,results,window)
plt = forecasts.ix[-30:,:4].plot()
plt.axvline(forecasts.index[-5])
# plot the estimators
#--------------------    
#posActivity = 5
#plot = plots.plot_Residual_corr(df.ix[:,0:maxAttr],results,4,posActivity)   

# Save in BigQuery
#-------------------- 
dfSave = forecasts
dfSave['timestamp'] = forecasts.index
gbq.to_gbq(dfSave,globe.PRStable,globe.PRSid,if_exists='replace')
dfLoad = pd.read_gbq("Select * FROM ["+globe.PRStable+"]", globe.PRSid)
dfLoad = dfLoad.set_index(['timestamp']).sort_index()
NextFlow = int(dfLoad.Flow[-5])
dfLoad.Flow[-5:].plot()
"""    

