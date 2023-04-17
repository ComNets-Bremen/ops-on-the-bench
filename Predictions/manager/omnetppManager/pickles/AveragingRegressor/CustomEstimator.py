import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm, skew, johnsonsu, lognorm
from scipy.special import boxcox1p,inv_boxcox1p
from sklearn.ensemble import RandomForestRegressor,  GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb
from sklearn.base import BaseEstimator, TransformerMixin,RegressorMixin,clone
import warnings
import pickle
# import time
warnings.filterwarnings('ignore')
# pd.set_option('display.max_columns',None)


df = pd.read_csv(r'C:\Users\srika\OneDrive\Desktop\Thesis_ppt\dataNEW.csv')

# df = df[~(df.peakdiskspaceusedbytes>(df.peakdiskspaceusedbytes.mean()+4*df.peakdiskspaceusedbytes.std()))]
# df = df[~(df.peakramusedsimbytes>(df.peakramusedsimbytes.mean()+4*df.peakramusedsimbytes.std()))]
# df = df[~(df.peakramusedresultsbytes>(df.peakramusedresultsbytes.mean()+4*df.peakramusedresultsbytes.std()))]
# df = df[~(df.totaljobclocktimesec>(df.totaljobclocktimesec.mean()+4*df.totaljobclocktimesec.std()))]
# # df.drop_duplicates(inplace=True)
# df.reset_index(inplace=True,drop=True)


df = df[(df.numNodes!=0)]
df.reset_index(inplace=True,drop=True)
print(df.shape)

# Different coulmn categories
Numericals = ['app_dataGenerationInterval','constraintAreaMaxX','constraintAreaMaxY','mobility_noOfLocations','mobility_Hosts','mobility_speed','numNodes','app_dataSizeInBytes','forwarding_maximumCacheSize','mobility_nodeId']
Categoricals = ['applicationLayer','forwardingLayer','linkLayer','mobilityType']
Targets = ['peakdiskspaceusedbytes','peakramusedsimbytes','peakramusedresultsbytes','totaljobclocktimesec']

## Skewness of all features

# Check the skew of all numerical features
skewed_feats = df[Numericals].apply(lambda x: skew(x)).sort_values(ascending=False)
print("\nSkew in numerical features: \n")
skewness = pd.DataFrame({'Skew' :skewed_feats})
# print(skewness)

## Applying BoxCox transforms

skewness = skewness[abs(skewness['Skew'].values) > 0.75]
print("There are {} skewed numerical features to Box Cox transform".format(skewness.shape[0]))


skewed_features = skewness.index
lam = 0.15
for feat in skewed_features:
  print(feat)
  #all_data[feat] += 1
  df[feat] = boxcox1p(df[feat], lam)

## Skewness of all features

# Check the skew of all numerical features
skewed_feats = df[Numericals].apply(lambda x: skew(x.dropna())).sort_values(ascending=False)
print("\nSkew in numerical features: \n")
skewness = pd.DataFrame({'Skew' :skewed_feats})
# print(skewness)

X = df.drop(Targets,axis=1)
y = boxcox1p(df[Targets],0.20)

x_train,x_test,y_train,y_test = train_test_split(X,y,test_size=0.1)

train_scalar1 = StandardScaler()

train_scalar2 = StandardScaler()

print(len(x_train.columns),x_train.columns)

x_train_scaled = pd.DataFrame(data=train_scalar1.fit_transform(x_train),columns=x_train.columns,index=x_train.index)
y_train_scaled = pd.DataFrame(train_scalar2.fit_transform(y_train),columns=y_train.columns,index=y_train.index)

x_test_scaled = pd.DataFrame(data=train_scalar1.transform(x_test),columns=x_test.columns,index=x_test.index)
y_test_scaled = pd.DataFrame(train_scalar2.transform(y_test),columns=y_test.columns,index=y_test.index)

# x_train_scaled,x_val_scaled,y_train_scaled,y_val_scaled = train_test_split(x_train_scaled,y_train_scaled,test_size=0.1)


GBoost = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.01,
                                   max_depth=4, max_features='sqrt',
                                   min_samples_leaf=15, min_samples_split=10,
                                   loss='huber', random_state =5)

model_xgb = xgb.XGBRegressor(colsample_bytree=0.4603, gamma=0.0468,
                             learning_rate=0.01, max_depth=3,
                             min_child_weight=1.5, n_estimators=2200,
                             reg_alpha=0.4640, reg_lambda=0.8571,
                             subsample=0.5213, silent=1,
                             random_state =7, nthread = -1)

model_lgb = lgb.LGBMRegressor(objective='regression',num_leaves=5,
                              learning_rate=0.01, n_estimators=720,
                              max_bin = 55, bagging_fraction = 0.8,
                              bagging_freq = 5, feature_fraction = 0.2319,
                              feature_fraction_seed=9, bagging_seed=9,
                              min_data_in_leaf =6, min_sum_hessian_in_leaf = 11)


class AveragingModels(BaseEstimator, RegressorMixin, TransformerMixin):
    def __init__(self, models):
        self.models = models
        self.models2 = models
        self.models3 = models
        self.models4 = models

    # we define clones of the original models to fit the data in
    def fit(self, X, y):
        self.models_ = [clone(x) for x in self.models]
        self.models2_ = [clone(x) for x in self.models2]
        self.models3_ = [clone(x) for x in self.models3]
        self.models4_ = [clone(x) for x in self.models4]
        self.clone_models = [self.models_, self.models2_, self.models3_, self.models4_]
        # Train cloned base models
        for model, model2, model3, model4 in zip(self.models_, self.models2_, self.models3_, self.models4_):
            model.fit(X, y[0])
            model2.fit(X, y[1])
            model3.fit(X, y[2])
            model4.fit(X, y[3])
        return self

    # Now we do the predictions for cloned models and average them
    def predict(self, X):
        predictions = np.column_stack([
            model.predict(X) for model in self.models_
        ])
        predictions2 = np.column_stack([
            model.predict(X) for model in self.models2_
        ])
        predictions3 = np.column_stack([
            model.predict(X) for model in self.models3_
        ])
        predictions4 = np.column_stack([
            model.predict(X) for model in self.models4_
        ])
        return [np.mean(predictions, axis=1), np.mean(predictions2, axis=1), np.mean(predictions3, axis=1),
                np.mean(predictions4, axis=1)]

CE2 = AveragingModels((model_xgb, GBoost))
_ = CE2.fit(x_train_scaled,[y_train_scaled.iloc[:,0],y_train_scaled.iloc[:,1],y_train_scaled.iloc[:,2],y_train_scaled.iloc[:,3]])

CE2_df = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(pd.DataFrame(CE2.predict(x_test_scaled)).transpose()),0.20),columns=y_test_scaled.columns,index=y_test_scaled.index)
print(CE2_df.head())

pickle.dump(CE2,open('CharmStackReg.pkl','wb'))
pickle.dump(train_scalar2,open('CharmEstTargetScalar.pkl','wb'))
pickle.dump(train_scalar1,open('CharmEstFeatureScalar.pkl','wb'))
