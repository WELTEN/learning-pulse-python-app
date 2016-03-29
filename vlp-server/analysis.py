
# -*- coding: utf-8 -*-

#   IMPORT
#*******************************************

from __future__ import division
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
#from pandas.tools.plotting import scatter_matrix
#from scipy.fftpack import fft
from scipy.stats import entropy
from scipy import signal
from pandas.stats.api import ols
import statsmodels.api as sm

# RF Regressor + interpreter
from sklearn.ensemble import RandomForestRegressor
from treeinterpreter import treeinterpreter as ti
#from sklearn.ensemble import RandomForestClassifier 
#from sklearn.naive_bayes import GaussianNB
#from sklearn.neighbors import KNeighborsClassifier
#from sklearn.svm import SVC


#   VARIABLES
#*******************************************
project_id = "xxx"
table_name = "xxx"

#Date boundaries today
today = datetime.utcnow().strftime('%Y-%m-%d')
yesterday = (datetime.today() - timedelta(1)).strftime('%Y-%m-%d')
startDay = '2015-11-23'
endDay = '2015-12-09'
n_bins = 10


#   FUNCTIONS
#*******************************************
def flowProdPoints(c): 
    return float(c['Flow']+c['Productivity'])/2

# Function to label the Flow points with corresponding values
def FPSscore(c):
    fp1 = float((100-c['Stress'])+c['Productivity'])/2
    return int((fp1+c['Flow'])/2)

# Function to label the Flow points with corresponding values
def FPSclass(c):
    if c['FPS']>33 and c['FPS']<=66:
        class_id = 2
    elif c['FPS']>66 and c['FPS']<=100:
        class_id = 3
    else:
        class_id = 1
    return class_id    

# Function to label the Flow points with corresponding values
def antiStress(c):
    return (100-c['Stress'])

# Function to label the Flow points with corresponding values
def flowPoints(c): 
    n = 100-abs(c['Abilities']-c['Challenge'])
    d = float(c['Abilities']+c['Challenge'])/2
    return int(n*d/100)
    
def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x'], point['y'], str(point['val']))
        
def HR_entropy(x):
    return entropy(np.histogram(x, bins=10)[0])

def nextpow2(n):
    m_f = np.log2(n)
    m_i = np.ceil(m_f)
    return 2**m_i
   
def HR_variability(y):
    nfft = nextpow2(len(y))
    F, PSD = signal.welch(y, nfft=nfft, return_onesided=True)
    intLF = np.where((F>0.04) & (F<0.15)) #Low frequencies
    intHF = np.where((F>0.15) & (F<0.4)) #High frequncies
    binsize = 1.0#F[1]-F[0]
    # check http://www.mit.edu/~gari/CODE/ECGtools/ecgBag/calc_lfhf.m
    LF = binsize * np.sum(PSD[intLF])
    HF = binsize * np.sum(PSD[intHF])
    return LF/HF
    """   
    # OLD Heart-Rate Variability
    # -----------------------
    L = 30*60 
    # The signal of the first half hour
    hour_signal = HRrsh['24/11/2015 08:00:00':'24/11/2015 08:30:00']
    # The number of transformations
     
    Y = fft(hour_signal,NFFT)/L
    f = np.array(1000/2*np.linspace(0,1,NFFT/2+1))
    Yf = np.array(2*abs(Y[0:NFFT/2]))
    #plt.plot(f,Yf) 
        
     
    #%AR_order = 12;
    nfft = 2^nextpow2(length(y));
    len()
    #% [PSD,F]=pburg(y,AR_order,(nfft*2)-1,Fs,'onesided');
    
    [PSD,F] = pwelch(y,[],[],[],4,'onesided');
    
    % [FTy] = fft(y,nfft);
    % F = (0:nfft-1)*Fs/nfft;
    % PSD = FTy.^2;
    figure,
    % Power Spectral Density
    plot(F,PSD,'r')
    title('PSD - spontaneous breathing','FontSize',12)
    xlabel('frequency (Hz)','FontSize',12)
    ylabel('n.u.','FontSize',12)
     
    % check intervals for LF and HF
    intLF = find(F>0.9 && F<0.12);
    intHF = find(F>0.12 && F<0.30);
    IndSVB = sqrt(PSD(intLF)/PSD(intHF));
     
    % sample entropy over 5 minutes
    % bin size of the PSD so that we can calculate the LF and HF metrics
    binsize=Fx(2)-Fx(1);
    
    % find the indexes corresponding to the LF and HF regions
    indl = find( (Fx>=LF_lo) & (Fx<=LF_hi) );
    indh = find( (Fx>=HF_lo) & (Fx<=HF_hi) );
    
    % calculate metrics
    lf   = binsize*sum(Px(indl));
    hf   = binsize*sum(Px(indh));
    lfhf =lf/hf;
    """

def long_pos_run(y):
    if y.empty:
        return None
    else:
        y = (y > y.shift()) # strictly monotonic
        return max(y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1))
    
def long_neg_run(y):
    if y.empty:
        return None
    else:
        y = (y < y.shift()) # strictly monotonic
        return max(y * (y.groupby((y != y.shift()).cumsum()).cumcount() + 1)) 

def avg_change(y):
    return y.diff().abs().mean()
    
def _argmin(y):
    if y.empty:
        return None
    else:
        return y.argmin()
 
def _argmax(y):
    if y.empty:
        return None
    else:
        return y.argmax()
        
hr_features = {'hr_mean':np.mean, 'hr_max':np.max, 'hr_min':np.min, 'hr_std':np.std, 'hr_avc':avg_change, 'hr_lpr':long_pos_run, 'hr_lnr':long_neg_run}    
        
# SCRIPT
#*******************************************
   
for i in range(7,8):
    
    user = "Arlearn"+str(i)
    print "Analysis for <arlearn"+str(i)+"@gmail.com>"
    
    # --------------------
    #/    RATINGS        /
    #--------------------
    
    # Collect all the ratings    
    RTquery = "SELECT *  FROM "+table_name+" WHERE " \
    "origin = 'rating' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+startDay+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+endDay+" 20:00:00') ORDER by timestamp"
    
    # Populating the dataframe 
    RTframe = pd.read_gbq(RTquery, project_id) 
    # Filtering the results
    RTdf = RTframe[['timestamp','objectId','resultResponse','lat','lng']]
    #Rename the columns
    RTdf.rename(columns={'objectId':'Indicators'}, inplace=True)
    RTdf.rename(columns={'resultResponse':'value'}, inplace=True)    
    #Reshape the DataFrame
    RTrsh = RTdf.set_index(['timestamp','Indicators'])['value']
    # In case of duplicates     
    RTrsh = RTrsh.drop(RTrsh.index.get_duplicates())
    RTrsh = RTrsh.unstack() 
    
    # Fix: the index will shift -1 hr. E.g. 9:00 -> 8:00 
    # Indicating the rating done at 9:00 for the 8:xx activities    
    RTrsh.index = RTrsh.index-pd.offsets.Hour(1)

    # 1. First check for missing values and fill them backward
    # 2. Then check again and fill them forward (workaround for latest missing)
    # 3. Then cast to int
    RTrsh[['Abilities','Challenge','Productivity','Stress']] = RTrsh[
        ['Abilities','Challenge','Productivity','Stress']].fillna(method='bfill'
        ).fillna(method='pad').astype(int) 
        
    # Calculate the Flow-Score - see function flowPoints for explaination   
    RTrsh['Flow'] = RTrsh.apply(flowPoints, axis=1)
    RTrsh['FlowProd'] = RTrsh.apply(flowProdPoints, axis=1)
    RTrsh['FPS'] = RTrsh.apply(FPSscore, axis=1)
    RTrsh['Stress'] = RTrsh.apply(antiStress, axis=1)
    RTrsh['class'] = RTrsh.apply(FPSclass, axis=1)
    # The correlation between Flow and Productivity 
    flowProdCorr = RTrsh[['Productivity','Flow']].corr().iloc[0]['Flow']
    
    # RATING PLOTS OK!
    #**************   
    
    # Polyigon in the plot which marks the Flow Zone
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2)
    
    # 1) Scatter Plot of the Flow 
    """
    RTplt1 = RTrsh.plot(x='Abilities',y='Challenge',
        kind='scatter', c='Flow', s=50, cmap=plt.cm.RdYlGn, title='Flow plot of '+user,
        colorbar=True) 
    RTplt1.set_xlim(-5,105)
    RTplt1.set_ylim(-5,105)
    RTplt1.add_patch(flowZone)
    RTplt1.set_xlabel("Abilities")
    RTplt1.set_ylabel("Challenge")
    """
    # In case we need to label the points in the scatter    
    #label_point(RTrsh.Abilities, RTrsh.Challenge, RTrsh.Flow, RTplt1)

    
    # 2) Scatter Plot of the Flow with Productivity as color intensity
    """
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2)    
    RTplt2 = RTrsh.plot(x='Abilities',
        y='Challenge', kind='scatter', c='Productivity', s=50, cmap=plt.cm.Blues,
        title='Productivity in the Flow of '+user, colorbar=True) 
    RTplt2.set_xlim(-5,105)
    RTplt2.set_ylim(-5,105)
    RTplt2.add_patch(flowZone)
    """
    # 3) Scatter Plot of the Flow with Productivity as color intensity
    """
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2)
    RTplt3 = RTrsh.plot(x='Abilities',
        y='Challenge', kind='scatter', c='FlowProd', s=50, cmap=plt.cm.BuGn,
        title='FlowProductivity average '+user, colorbar=True) 
    RTplt3.set_xlim(-5,105)
    RTplt3.set_ylim(-5,105)
    RTplt3.add_patch(flowZone)
    """
    
    # 4) Scatter Plot of the FPS score
    """
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2)
   
    RTplt4 =  RTrsh[['Abilities','Challenge','FPS']].plot(x='Abilities',
        y='Challenge', kind='scatter', c='FPS', s=50, cmap=plt.cm.BuGn,
        title='FPS score '+user, colorbar=True) 
    RTplt4.set_xlim(-5,105)
    RTplt4.set_ylim(-5,105)
    RTplt4.add_patch(flowZone)  
    """
    
    # 3) Scatter plot of the Productivity against the Flow
    #RTplt5_title = "Flow vs Productivity of "+user+" (corr=%f)" % flowProdCorr
    #RTplt5 = sns.jointplot("Productivity", "Flow", data=RTrsh, kind="reg", 
    #                       color="b", xlim=(-5,105), ylim=(-5,105))    
                           
    # 4) Scatter matrix with Productivity Stress and Flow
    #RTPlot4 = sns.PairGrid(RTrsh[['Productivity','Stress','Flow']], diag_sharey=False)
    #RTPlot4.map_lower(sns.kdeplot, cmap="Blues_d")
    #RTPlot4.map_upper(plt.scatter)
    #RTPlot4.map_diag(sns.kdeplot, lw=1)

    
    # --------------------
    #/    STEP COUNTS    /
    #--------------------
    # Step count query builder
    SCquery = "SELECT *  FROM "+table_name+" WHERE " \
    "objectID = 'StepCount' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+startDay+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+endDay+" 20:00:00') ORDER by timestamp"
    
    SCframe = pd.read_gbq(SCquery, project_id) # Populating the dataframe
    SCdf = SCframe[['timestamp','resultResponse']]  # Filtering the results 
    SCrsh = SCdf.set_index(['timestamp']).astype(int) #timestamp as index
    SCrsh.rename(columns={'resultResponse':'Steps'}, inplace=True) #Rename columns
    #Group Step count instances by taking the sum
    SCrsh = SCrsh.groupby(pd.TimeGrouper('5Min'))['Steps'].sum() 
     
    # --------------------
    #/    HEART RATE     /
    #--------------------       
    # Heart rate query builder           
    HRquery = "SELECT *  FROM "+table_name+" WHERE " \
    "objectID = 'HeartRate' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+startDay+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+endDay+" 20:00:00') ORDER by timestamp"
    
    HRframe = pd.read_gbq(HRquery, project_id) # Populating the dataframe
    HRdf = HRframe[['timestamp','resultResponse']]
    HRrsh = HRdf.set_index(['timestamp']).astype(int)  #timestamp as index
    
    # Heart Rate Entropy Calculation   
    # -----------------------------
    HR5S = HRrsh.resample('5S').interpolate()
    #HRrsh['HR'] = HRrsh['HR'].astype('int') #back to int
    HRent = HR5S.resample('5Min', how={'resultResponse': HR_entropy})  
    HRent.rename(columns={'resultResponse':'HRE'}, inplace=True)    
    
    # Heart Rate Variability Calculation
    # -----------------------------
    #HR1S = HRrsh.resample('1S').interpolate()  
    #HRvar = HR1S.resample('5Min', how={'resultResponse': HR_variability}) 
    #HRvar.rename(columns={'resultResponse':'HRV'}, inplace=True)  
    
    # --------------------
    #/    ACTIVITIES     /
    #--------------------    
    
    ACquery = "SELECT *  FROM "+table_name+" WHERE " \
    "origin = 'rescuetime' AND actorID='mailto:arlearn"+str(i)+"@gmail.com' " \
    " AND timestamp > PARSE_UTC_USEC('"+startDay+" 07:00:00') AND timestamp < " \
    " PARSE_UTC_USEC('"+endDay+" 20:00:00') ORDER by timestamp"
    
    ACframe = pd.read_gbq(ACquery, project_id) # Populating the dataframe 
    ACframe['origin'] = ACframe['origin'].astype(str)
    ACdf = ACframe[['timestamp','objectId','resultDuration']]
    ACdf.rename(columns={'objectId':'App'}, inplace=True)  
    ACrsh = ACdf.groupby(['timestamp', 'App'])['resultDuration'].sum().unstack()
    ACrsh = ACrsh.fillna(0)
    
    #To know the most used applications    
    #sum(axis=0).sort_values(ascending=False).head(10)
    
     # --------------------
    #/    WEATHER     /
    #--------------------  
    wdata = pd.read_csv('weather_data.csv',index_col=13,parse_dates=True)
    WDdf = wdata[['TemperatureC','Humidity','Sea Level PressurehPa',
                 'Conditions']]
    WDdf.index = WDdf.index + pd.DateOffset(hours=1)
    WDdf.rename(columns={'DateUTC':'Date','TemperatureC':'Temp','Sea Level PressurehPa':
    'Pressure'}, inplace=True)
    condLegend =  WDdf['Conditions']
    WDdf['Conditions'] = WDdf['Conditions'].astype('category').cat.codes
    
    # --------------------
    #/    MERGE          /
    #--------------------       
    DV = pd.concat([RTrsh[['Abilities','Challenge','Productivity','Stress']],
                    HRent, SCrsh],axis=1)
    # Fill the NULL values BACKWARD
    DV[['Abilities','Challenge','Productivity','Stress']] = DV[['Abilities',
    'Challenge','Productivity','Stress']].fillna(method='bfill')
    
    # Delete all the NULL values 
    DV = DV.dropna()
    
    # Join LEFT the weather data     
    DV = DV.join(WDdf,how='left')
    
    # Fill the NULL values FORWARD
    DV[['Temp','Humidity','Pressure','Conditions']] = DV[['Temp',
        'Humidity','Pressure','Conditions']].fillna(method='pad')
    
    # Join LEFT with the Activity data
    DV = DV.join(ACrsh,how='left') #inner join method
    
    # Exponential Weighted Moving Average
    #-------------------------------------
    #http://pandas.pydata.org/pandas-docs/stable/generated/pandas.ewma.html
    # Center of Mass      
    #com =  (span - 1)/2
    span = 12 
    output_no = 4     
    DVewma = pd.DataFrame() 
    for g in DV.groupby([DV.index.year,DV.index.month,DV.index.day]):
        DVewma = DVewma.append(pd.ewma(g[1],span=span))  
    DVewma.sort_index(inplace=True)
    DVewma.fillna(0,inplace=True)
        
    DVpred = DVewma.ix[:,5:len(DVewma.columns)]
    DVpred = pd.concat([DVpred,DV[['Abilities','Challenge','Productivity','Stress']]],axis=1)
    #Since Condition is categorical restore the initial value
    DVpred['Conditions'] = DV['Conditions'] 
    
    #Remove the cold start instances! i.e. when the instances Rescue Time data
    # all sums up to 0
    DVpred = DVpred[(DVpred.ix[:,7:len(DVpred.columns)-output_no].T != 0).any()]
    #Random permutation    
    DVpred = DVpred.reindex(np.random.permutation(DVpred.index))
    
    # --------------------
    #/   REGRESSION       /
    #-------------------- 
    
    # Linear regression method
    #res = ols(y=DV['FPS'], x=DV.ix[:,5:len(DV.columns)], window=25)
    pc_train = 0.90 # not necessary with out-of-bag model
         
    features = DVpred.ix[:,0:len(DVpred.columns)-output_no].as_matrix()
    feature_names = DVpred.columns.values[:-output_no].astype(str)
    labels = DVpred.ix[:,len(DVpred.columns)-output_no:len(DVpred.columns)]
    training_size = int(features.shape[0]*pc_train)
    test_size = features.shape[0] - training_size
    X_train = features[0:training_size,:]
    y_train = labels[0:training_size]
    X_test = features[training_size:features.shape[0],:]
    y_test = labels[training_size:features.shape[0]]
    
    # Random Forest
    #--------------------#
    rng = np.random.RandomState(0)
    forest = RandomForestRegressor(max_depth=10, n_estimators=100, oob_score=True,
                                   n_jobs=-1,random_state=rng)
    #add out of bag, add randomization 
    forest = forest.fit(features,labels)
    #score = forest.score(X_test,y_test)
    score = forest.oob_score_
    print ("Random forest score: %f" % score)
    print ("Tree interpretation...")
    
    # --------------------
    #/ Feature ranking   /
    #-------------------- 
    ft_n = 10
    ft_offset = 6
    importances = forest.feature_importances_
    std = np.std([tree.feature_importances_ for tree in forest.estimators_],
                 axis=0)
    indices = np.argsort(importances)[::-1]
    X = features 
    # Print the feature ranking
    print("Feature ranking:")
    
    for f in range(X.shape[1]):
        print("%s (%f)" % (feature_names[f], importances[indices[f]]))
    
    # Plot the feature importances of the forest
    plt.figure()
    plt.title("Feature importances")
    plt.bar(range(ft_n), importances[indices[ft_offset:ft_n+ft_offset]],
           color="r", yerr=std[indices[ft_offset:ft_n+ft_offset]], align="center")
    plt.xticks(range(10), feature_names[ft_offset:ft_n+ft_offset],rotation=70)
    plt.xlim([-1, ft_n])
    plt.show()



    # --------------------
    #/   SAVING RESULTS   /
    #--------------------
     
    #titlecsv = "FPSclass"+str(i)+"@gmail.com_"+today    
    #RTrsh[['Productivity','Flow','Stress','class']].to_csv(titlecsv+".csv")