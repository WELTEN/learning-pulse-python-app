# -*- coding: utf-8 -*-
"""
Created on Mon Mar 21 21:10:56 2016
@author: Daniele Di Mitri ddm@ou.nl
@title: plots.py
"""
# --------------------
#/    PLOTS          /
#--------------------

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from itertools import chain, repeat

# Assistant function to label points
def label_point(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x'], point['y'], str(point['val']))

# 1) Scatter Plot of the Flow     
def plot_Flow(df,user):
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2)
    plot = df.plot(x='Abilities',y='Challenge',
        kind='scatter', c='Flow', s=50, cmap=plt.cm.RdYlGn, title='Flow plot of '+user,
        colorbar=True) 
    plot.set_xlim(-5,105)
    plot.set_ylim(-5,105)
    plot.add_patch(flowZone)
    plot.set_xlabel("Abilities")
    plot.set_ylabel("Challenge")
    # In case we need to label the points in the scatter    
    label_point(df.Abilities, df.Challenge, df.Flow, plot)
    return plot
    
# 2) Scatter Plot of the Flow with Productivity as color intensity
def plot_FlowProd(df,user):  
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2)
    plot = df.plot(x='Abilities',
        y='Challenge', kind='scatter', c='FlowProd', s=50, cmap=plt.cm.BuGn,
        title='FlowProductivity average '+user, colorbar=True) 
    plot.set_xlim(-5,105)
    plot.set_ylim(-5,105)
    plot.add_patch(flowZone)
    return plot 
    
 # 3) Scatter Plot of the FPS score
def plot_FlowFPS(df,user):     
    flowZone = plt.Polygon([(50,50), (75,105), (105,105), (105,75)],alpha=0.2) 
    plot =  df[['Abilities','Challenge','FPS']].plot(x='Abilities',
        y='Challenge', kind='scatter', c='FPS', s=50, cmap=plt.cm.BuGn,
        title='FPS score '+user, colorbar=True) 
    plot.set_xlim(-5,105)
    plot.set_ylim(-5,105)
    plot.add_patch(flowZone) 
    return plot
    
# 4) Scatter plot of the Productivity against the Flow    
def plot_FlowProd_corr(df,user,corr):
    plot = "Flow vs Productivity of "+user+" (corr=%f)" % corr
    plot = sns.jointplot("Productivity", "Flow", data=df, kind="reg", 
                           color="b", xlim=(-5,105), ylim=(-5,105))
    return plot
    
# 5) Plot of the Residual correaltions     
def plot_Residual_corr(df,results,posTarget,fromFeauture):
    #the flow correlation matrix
    d = dict(zip(df.columns[fromFeauture:], 
                 chain(results.resid_corr[posTarget,fromFeauture:], 
                       repeat(None))))          
    nd = sorted(d.items(), key=lambda x: x[1],reverse=True)   
    apps = zip(*nd)[0]
    score = zip(*nd)[1]
    x_pos = np.arange(len(apps))    
    plt.bar(x_pos, score,align='center')
    plt.xticks(x_pos, apps, rotation=70) 
    plt.show()