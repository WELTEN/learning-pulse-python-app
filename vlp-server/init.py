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
  
regenerate = True

if regenerate: 
    # Fetch and transform User data from the Learning Record Store
    df_original = fetchData(globe.start_second_experiment,globe.end_second_experiment)
    df_original_flat = df_original.reset_index()
    gbq.to_gbq(df_original_flat,globe.PRStable,globe.PRSid,if_exists='replace')
else:
    # download from BigQuery    
    df_original_flat =  pd.read_gbq("Select * FROM ["+globe.PRStable+"]", globe.PRSid)
    df_original = df_original_flat.set_index(['timestamp','actorId']).sort_index()

window = 5 # number of timeframe to predict

actors = df_original_flat.actorId.unique().tolist()
if 10 in actors: actors.remove(10)
max_flows = pd.DataFrame(np.nan, index=actors, columns=['Flow'])
min_flows = pd.DataFrame(np.nan, index=actors, columns=['Flow'])

categoricals = ['MainActivity','lat','lng','weatherId','Steps'] 
activities = list(df.ix[:,19:].columns.values)

#prepare the future dataframe
df_future = pd.DataFrame() 

#VAR specific to each participant
for user in actors:
    
    df_pred = pd.DataFrame() 
    df = df_original.xs(user,level='actorId')
    max_flows.Flow[user] = max(df.Flow)
    min_flows.Flow[user] = min(df.Flow)
    #Selecting features to feed in the VAR process
    dt = df[fixed_effects]    
    VARres = VARprocess(dt)    
    forecasts = VARforecast(dt,VARres,window)    
    forecasts['actorId'] = user
    #Forecast plots    
    plt = forecasts.plot()
    plt.axvline(forecasts.index[-window])  
    
    # Prediction table
    df_pred = df.append(forecasts)
    
    #Fill NaN strategy
    #-----------------
    # timeframe
    forecasts['timeframe'] = forecasts.index.hour
    #df_pred[categoricals + activities] = df_pred[categoricals + activities].fillna(method='pad')                  
    #df_pred['actorId'] = user
    df_future = df_future.append(forecasts)  

df_future = df_future.reset_index().set_index(['index','actorId']).sort_index()
df_future_flat = df_future.reset_index()   
    
# Model Learning
#-------------------- 
random_effects = activities + ['Steps']
fixed_effects =  ['pressure', 'temp', 'humidity', 'hr_min', 'hr_avc', 'hr_mean',
                  'hr_std', 'hr_max', 'timeframe']
labels = ['Abilities', 'Challenge', 'Productivity', 'Stress']
data['intercept'] = 1
LMEM_models = []
endog = data[target]
exog = data[fixed_effects + ['intercept']]
exog_re = data[random_effects]
groups = data['actorId']
for target in labels:
    LMEM = sm.MixedLM(endog, exog, groups=groups, exog_re=exog_re).fit()
    LMEM_models.append(LMEM)
    print(LMEM.summary(LMEM))
    

#Coefficients importance averaging
coeff = pd.DataFrame(index=range(0,len(exog.T)),data={'coefficients':0.0}, dtype='float').coefficients
for i in range(0,len(coeff)):
    for j in range(0,len(LMEM_models)):
        coeff[i] = coeff[i]+LMEM_models[j].fe_params[i]
coeff = coeff/len(LMEM_models)

for i in range(0,len(labels)):
    df_future[labels[i]] = LMEM_models[i].predict(df_future[fixed_effects + ['intercept']])
df_future['Flow'] = df_future.apply(flowPoints, axis=1)
df_future['Flow_norm'] = df_future['Flow']/df_future['actorId']

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

