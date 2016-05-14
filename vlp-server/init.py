# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: init.py
"""
from core import *
import globe
import plots
import warnings

# Import global names
globe.setGlobalNames()
  
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

star_date = globe.end_second_experiment

    
# Actors definition
#-------------------------------
#count participants anre remove 10
actors = df_original_flat.actorId.unique().tolist()
if 10 in actors: actors.remove(10)

# Attributes definition
#-------------------------------
categoricals = ['MainActivity','lat','lng','weatherId','Steps'] 
activities = list(df_original.ix[:,19:].columns.values)
random_effects = activities + ['Steps']
fixed_effects =  ['pressure', 'temp', 'humidity', 'hr_min', 'hr_avc', 'hr_mean',
                  'hr_std', 'hr_max', 'timeframe']
labels = ['Abilities', 'Challenge', 'Productivity', 'Stress', 'Flow']
   
target_min = pd.DataFrame(np.nan, index=actors, columns=labels)
target_max = pd.DataFrame(np.nan, index=actors, columns=labels)
target_mean = pd.DataFrame(np.nan, index=actors, columns=labels)
target_std = pd.DataFrame(np.nan, index=actors, columns=labels)

# VAR on fixed effects 
#-------------------------------
window = 5  # Windows to predict
df_future = pd.DataFrame() #prepare the future dataframe
var_attributes = [item for item in fixed_effects if item not in ['timeframe']]
for user in actors:    
    df_user = df_original.xs(user,level='actorId')
    df = df_user[var_attributes]     
    VARres = VARprocess(df)    
    forecasts = VARforecast(df,VARres,window)        
    #plt = forecasts.plot() # prediction plot
    #plt.axvline(forecasts.index[-window])  
    forecasts['actorId'] = user
    forecasts['timeframe'] = forecasts.index.hour                      
    df_future = df_future.append(forecasts)  
    # offtopic, add max and min
    for target in (labels):   
        target_min[target][user] = min(df_user[target])
        target_max[target][user] = max(df_user[target])
        target_mean[target][user] = df_user[target].mean()
        target_std[target][user] = df_user[target].std()

df_future['Intercept'] = 1

df_future = df_future.reset_index().set_index(['index','actorId']).sort_index()
# ------------------------------- end VAR
    
# Linear Mixed Effect Model
# ------------------------------- 
data = df_original_flat
data['intercept'] = 1 # set the intercept term
LMEM_models = [] # create a list of models, for multi output
exog = data[fixed_effects + ['intercept']] # the attributes from which to predict
exog_re = data[random_effects] # random effects
groups = data['actorId'] # group definition

# Training phase of four model, one per each label
for target in labels:
    endog = data[target] # endogenous, ie the values we want to predict
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        LMEM = sm.MixedLM(endog, exog, groups=groups, exog_re=exog_re).fit()
        LMEM_models.append(LMEM)
        #print(LMEM.summary(LMEM))
    
# Coefficients importance averaging
coeff = pd.DataFrame(index=range(0,len(exog.T)),data={'coefficients':0.0}, dtype='float').coefficients
for i in range(0,len(coeff)):
    for j in range(0,len(LMEM_models)):
        coeff[i] = coeff[i]+LMEM_models[j].fe_params[i]
coeff = coeff/len(LMEM_models)

# Test phase for each of the four models
df = df_future.reset_index()   
exog = df[fixed_effects]
exog['intercept'] = 1
for i in range(0,len(labels)):
    t = labels[i]
    df[t] = LMEM_models[i].predict(exog)
    # normalization
    for u in actors:
        actual = df[df['actorId']==u][t]
        rindex = df[df['actorId']==u][t].index
        # Normalization (x_max-x_min)*(x_i/100)+x_min
        df.loc[rindex,t] = (target_max[t][u] - target_min[t][u])*(actual/
        100)+target_min[t][u].astype('int')
# Save in BigQuery
gbq.to_gbq(df,globe.PRSforecast,globe.PRSid,if_exists='replace')
# ------------------------------- end LMEM