# -*- coding: utf-8 -*-
from sklearn.linear_model import ElasticNet
from sklearn.metrics import r2_score
"""
#Elastic net
new_df = pd.DataFrame() 
for group in df.groupby([df.index.year,df.index.month,df.index.day]):
    new_df = new_df.append(
        pd.concat(
            [group[1].ix[:,:15].resample('1D', how=np.mean),
             group[1].ix[:,15:].resample('1D', how=np.sum)],axis=1)
        )
new_df.sort_index(inplace=True)
X_train = new_df.ix[:7,1:]
X_test = new_df.ix[7:,1:]
y_train = new_df.ix[:7,0]
y_test = new_df.ix[7:,0]
enet = ElasticNet(alpha=0.1, l1_ratio=0.7)
y_pred_enet = enet.fit(X_train, y_train).predict(X_test)
r2_score_enet = r2_score(y_test, y_pred_enet)
print enet.coef_
print r2_score_enet
return enet.coef_,r2_score_enet
"""