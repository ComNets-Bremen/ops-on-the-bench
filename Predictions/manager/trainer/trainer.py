import numpy as np
import pandas as pd
import re
import glob
from scipy import stats
from scipy.stats import skew
from scipy.special import boxcox1p
from scipy.special import boxcox1p,inv_boxcox1p

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from sklearn.base import BaseEstimator, TransformerMixin,RegressorMixin,clone
from sklearn.ensemble import GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb

from keras.losses import mean_squared_error,mean_absolute_error,huber_loss
from keras.layers import LeakyReLU
LeakyReLU = LeakyReLU(alpha=0.1)

import time
import pickle
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns',None)
from pathlib import Path

# Function that takes in the JSON File and return a list of tuples where each tuple is (Run_Config, Omnetpp.ini, TargetsDictionary)
def JSONExtractor(JSON):
    runINI = []
    delINI = []
    ignore = []
    disk = "'peakdiskspaceusedbytes'"
    simRAM = "'peakramusedsimbytes'"
    resRAM = "'peakramusedresultsbytes'"
    time = "'totaljobclocktimesec'"

    for i in range(len(JSON)):

        # Checking if the Simulation_Completion and Results_Parsing_Completion are 100% and current state = 'COMPLETED'
        if ((JSON.simulations[i]['meta']['sim_completed_perc'] == 100) and (
                JSON.simulations[i]['meta']['results_completed_perc'] == 100) and (
                JSON.simulations[i]['meta']['current_state'] == 'COMPLETED')):

            # Checking if simulation contains meta data with 'sim_runtime_stats' as key (if not present 'totaljobclocktimesec' param can't be found, so discarding them)
            if 'sim_runtime_stats' in JSON.simulations[i]['meta']:

                # Fetching the all 4 targets variables from meta data of the simulation
                dicts = {'peakdiskspaceusedbytes': re.compile(disk + r'\,\s([0-9\.]+)').findall(
                    str(JSON.simulations[i]['meta']['sim_runtime_stats'])),
                         'peakramusedsimbytes': re.compile(simRAM + r'\,\s([0-9\.]+)').findall(
                             str(JSON.simulations[i]['meta']['sim_runtime_stats'])),
                         'peakramusedresultsbytes': re.compile(resRAM + r'\,\s([0-9\.]+)').findall(
                             str(JSON.simulations[i]['meta']['sim_runtime_stats'])),
                         'totaljobclocktimesec': re.compile(time + r'\,\s([0-9\.]+)').findall(
                             str(JSON.simulations[i]['meta']['sim_runtime_stats']))}

                # Appending Run_Config, Omnetpp.ini and Targets dictionary as a tuple in runINI list
                runINI.append((JSON.simulations[i]['runconfig'], JSON.simulations[i]['omnetppini'], dicts))
            else:
                ignore.append((JSON.simulations[i]['runconfig'], JSON.simulations[i]['omnetppini']))
        else:
            # print(i)
            # Appending info about incomplete simulations
            delINI.append((JSON.simulations[i]['runconfig'], JSON.simulations[i]['omnetppini'], dicts))

    return runINI

# Function that takes in Run_Config, .ini, TargetsDictionary and returns a dictionary of all .ini parameters
# of a simulation along with their corresponding targets
def FeatureExtractor(runconfig,omnetppini,targets):
  if not runconfig == 'General':
    # print(runconfig)
    # replacing multiple \r and \n with null and \n resp. and splitting on \n basis
    splitINI = re.sub(r'[\n]+','\n ',re.sub(r'[\r]+','',omnetppini)).strip().split('\n')

    # INI filtering (removes any redundant commands/comments starting with '#' in the ini)
    refreshINI = ''.join([line.strip() for line in splitINI if not line.strip().startswith('#')])

    # RunConfig Filtering (Filter INI for the specific RunConfig) --- case where multiple Run_Configs
    # are present in same ini file
    configFiltered = re.compile(runconfig + r'[\'\]\n\#\s\w\*\.=\(\)\"\,\-\/\+]+').findall(refreshINI)

    # Extracting every ini param and converting to dict
    paramDict = dict(re.findall(r'\*\*\.([a-zA-Z\.]+) = ([A-Za-z0-9\"\.\/\-]+)',str(configFiltered)))
    if 'numNodes' not in paramDict.keys():
      x = re.findall(r'\*\*\.(numNodes) = ([0-9]+)',refreshINI)[0]
      paramDict[x[0]] = x[1]

    # Combining .ini parameters dictionary with TargetsDictionary
    paramDict.update(targets)

    return paramDict


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

import os
import sys
from bs4 import BeautifulSoup

# dirpath = os.path.dirname(__file__)
# filepath = os.path.join(dirpath, 'simulation-meta_26_02_2023.json')
# print("filepath",dirpath)
# PATH to JSON data files directory
# path = "./directory"
# path = "S:\MS\Autonomous_Robots\Exercise_sheets\[1]_ex01_material\prob01_03"
# JSONDrives = glob.glob(f'{path}/*.json')
# print(len(JSONDrives))
# print(JSONDrives)

if __name__=='__main__':
    Finished_Jobs = 0
    html_file = str(sys.argv[1])
    html_file_path = os.path.join(os.getcwd(),html_file)
    print("HTML PATH ", html_file_path)
    HTMLfile = open(html_file_path,'r').read()
    S = BeautifulSoup(HTMLfile)
    table = S.find("table", attrs={"class": "table"})
    td_li = table.find_all("td")
    for td in td_li:
        if td.get_text() == "Finished jobs":
            Finished_Jobs = td.findNext().get_text()
    if int(Finished_Jobs)/30>1:
        print("Arguments ",sys.argv[2])
        file = str(sys.argv[2])
        JSONDrives = [os.path.join(os.getcwd(),file)]
        print(len(JSONDrives))

        finalDic = []
        inis = []
        runconfig = []
        for path in JSONDrives:
          try:
            json = pd.read_json(path)
            if len(json)!=0:
                JsonFiltered = JSONExtractor(json)
                # print("Initial Length of JSON",len(json),"Final Length of Filtered JSON",len(JsonFiltered))
                # ParamsList = []
                for rc,ini,targets in JsonFiltered:
                  # Feature Extractor function returns .ini params and targets as dictionary
                  dic = FeatureExtractor(rc,ini,targets)
                  if bool(dic):
                    # ParamsList.append(dic)
                    inis.append(ini)
                    runconfig.append(rc)
                    finalDic.append(dic)
            else:
                print("JSON is empty")
          except:
            print("Path Error")

        # Data Cleaning
        # Different column categories
        Numericals = ['app_dataGenerationInterval','constraintAreaMaxX','constraintAreaMaxY','mobility_noOfLocations','mobility_Hosts',
                      'mobility_speed','numNodes','app_dataSizeInBytes','forwarding_maximumCacheSize','mobility_nodeId']
        Categoricals = ['applicationLayer','forwardingLayer','linkLayer','mobilityType']
        Targets = ['peakdiskspaceusedbytes','peakramusedsimbytes','peakramusedresultsbytes','totaljobclocktimesec']

        first = pd.DataFrame(finalDic)

        for_null = first[first['forwardingLayer'].isna()]
        second = first[~first['forwardingLayer'].isna()]

        second.columns = second.columns.str.replace('.','_',regex=False)

        remove_cols = ['app_popularityAssignmentPercentage','app_usedRNG','forwarding_antiEntropyInterval','forwarding_maximumHopCount','forwarding_usedRNG','link_wirelessRange','link_neighbourScanInterval','link_bandwidthBitRate','link_wirelessHeaderSize','link_usedRNG','constraintAreaMinX','constraintAreaMinY','constraintAreaMinZ','constraintAreaMaxZ','updateInterval','mobility_initFromDisplayString','mobility_popularityDecisionThreshold','mobility_returnHomePercentage','mobility_neighbourLocationLimit','mobility_radius','mobility_alpha','mobility_waitTime','mobility_usedRNG','app_dataGenerationIntervalMode','app_trafficInfoPath','forwarding_spraywaitFlavour','forwarding_noDuplicate','mobility_traceFile','link_contactTracesPath','forwarding_broadcastRRS','forwarding_sendOnNeighReportingFrequency','forwarding_sendFrequencyWhenNotOnNeighFrequency','forwarding_pEncounterMax','forwarding_pEncounterFirst','forwarding_pFirstThreshold','forwarding_alpha','forwarding_beta','forwarding_gamma','forwarding_delta','forwarding_standardTimeInterval','forwarding_agingInterval','forwarding_neighbourhoodChangeSignificanceThreshold','forwarding_coolOffDuration','forwarding_learningConst','forwarding_backoffTimerIncrementFactor','app_specificDestination','app_specificDestinationNodeName','app_ttl','forwarding_useTTL']

        leftover_cols = [col for col in second.columns if col not in remove_cols]

        # Seprating dataframe with required columns
        third = second[leftover_cols]

        # Filling Missing Values and Replacing
        third.mobilityType = third.mobilityType.fillna("ContactTraces")
        third.mobility_nodeId = third.mobility_nodeId.fillna('0').str.replace('-1','1')
        third.constraintAreaMaxX = third.constraintAreaMaxX.fillna('0')
        third.constraintAreaMaxY = third.constraintAreaMaxY.fillna('0')
        third.mobility_noOfLocations = third.mobility_noOfLocations.fillna('0')
        third.mobility_Hosts = third.mobility_Hosts.fillna('0')
        third.mobility_speed = third.mobility_speed.fillna('0')
        third.forwarding_maximumCacheSize = third.forwarding_maximumCacheSize.fillna('0')

        # Creating ONE-HOTS for categorical (object) columns
        one_hots = pd.get_dummies(third[Categoricals],drop_first=True)
        fourth = pd.concat([third,one_hots],axis=1)
        fourth = fourth.drop(Categoricals,axis=1)

        # Changing Numerical features from strings to integers
        fourth['app_dataGenerationInterval'] =  fourth.app_dataGenerationInterval.apply(lambda x : x.replace('s','') if 's' in x else x)
        fourth['constraintAreaMaxX'] =  fourth.constraintAreaMaxX.apply(lambda x : x.replace('m','') if 'm' in x else x)
        fourth['constraintAreaMaxY'] =  fourth.constraintAreaMaxY.apply(lambda x : x.replace('m','') if 'm' in x else x)
        fourth['mobility_speed'] =  fourth.mobility_speed.apply(lambda x : x.replace('mps','') if 'mps' in x else x)
        def for_maxCache(cache):
          if 'bytes' in str(cache):
            return cache.replace('bytes','')
          elif 'byte' in str(cache):
            return cache.replace('byte','')
          else:
            return cache
        fourth['forwarding_maximumCacheSize'] =  fourth.forwarding_maximumCacheSize.apply(lambda x : for_maxCache(x))

        #Separating features from the dataset and changing their datatype
        features = fourth.drop(Targets,axis=1)
        fourth[features.columns] = features.apply(pd.to_numeric)

        # Changing Target variables from string to integers
        def target_list(target):
          if type(target) is list:
            return pd.to_numeric(target[0],errors='coerce')
        for col in Targets:
          fourth[col] = fourth[col].apply(lambda x: target_list(x))

        fourth.columns = fourth.columns.str.replace('"','')
        fourth = fourth.reset_index(drop=True)
        # print(fourth)

        #Save the dataset
        # fourth.to_csv('path.csv',index=False)
        fifth = fourth.copy(deep=True)

        ## Skewness of all features

        # Check the skew of all numerical features
        skewed_feats = fifth[Numericals].apply(lambda x: skew(x)).sort_values(ascending=False)
        print("\nSkew in numerical features: \n")
        skewness = pd.DataFrame({'Skew' :skewed_feats})
        print("Skewness in the independent variables ",skewness)

        ## Applying BoxCox transforms

        skewness = skewness[abs(skewness['Skew'].values) > 0.75]
        print("There are {} skewed numerical features to Box Cox transform".format(skewness.shape[0]))
        skewed_features = skewness.index
        lam = 0.15
        for feat in skewed_features:
          print(feat)
          fifth[feat] = boxcox1p(fifth[feat], lam)

        # Check the NEW skew of all numerical features
        skewed_feats = fifth[Numericals].apply(lambda x: skew(x.dropna())).sort_values(ascending=False)
        print("\nSkew in numerical features: \n")
        skewness = pd.DataFrame({'Skew' :skewed_feats})
        print("Skewness in the independent variables after transforms ",skewness)

        sixth = fifth.copy(deep=True)
        print(sixth)

        # PASS THE PREPROCESSED DATASET AS INPUT named as (SIXTH)
        X = sixth.drop(Targets,axis=1)
        y = boxcox1p(sixth[Targets],0.20)

        x_train,x_test,y_train,y_test = train_test_split(X,y,test_size=0.1,shuffle=True)

        train_scalar1 = StandardScaler()

        train_scalar2 = StandardScaler()

        x_train_scaled = pd.DataFrame(data=train_scalar1.fit_transform(x_train),columns=x_train.columns,index=x_train.index)
        y_train_scaled = pd.DataFrame(train_scalar2.fit_transform(y_train),columns=y_train.columns,index=y_train.index)

        x_test_scaled = pd.DataFrame(data=train_scalar1.transform(x_test),columns=x_test.columns,index=x_test.index)
        y_test_scaled = pd.DataFrame(train_scalar2.transform(y_test),columns=y_test.columns,index=y_test.index)

        x_train_scaled,x_val_scaled,y_train_scaled,y_val_scaled = train_test_split(x_train_scaled,y_train_scaled,test_size=0.1)

        print("Samples in Train set : ", len(x_train_scaled))
        print("Samples in Validation set : ", len(x_val_scaled))
        print("Samples in Test set : ", len(x_test_scaled))

        print("Shape of Train set : ", x_train_scaled.shape)
        print("Shape of Validation set : ", x_val_scaled.shape)
        print("Shape of Test set : ", x_test_scaled.shape)

        # Stats of targets in test dataset
        print(len(y_test))
        print(y_test.iloc[:,0].mean())
        print(y_test.iloc[:,0].std())

        #REGRESSORS
        GBoost = GradientBoostingRegressor(n_estimators=3000, learning_rate=0.01,
                                           max_depth=4, max_features='sqrt',
                                           min_samples_leaf=15, min_samples_split=10,
                                           loss='squared_error', random_state =5)

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

        CE2 = AveragingModels((model_xgb, GBoost, model_lgb))
        start_time = time.time()
        _ = CE2.fit(x_train_scaled,[y_train_scaled.iloc[:,0],y_train_scaled.iloc[:,1],y_train_scaled.iloc[:,2],y_train_scaled.iloc[:,3]])
        end_time = time.time()
        print("Time taken for the average model to train", end_time-start_time)

        #Inferences
        CE2_df = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(pd.DataFrame(CE2.predict(x_test_scaled)).transpose()),0.20),columns=y_test_scaled.columns,index=y_test_scaled.index)
        y_test_org = inv_boxcox1p(y_test,0.20)

        # PERFORMANCE METRICS of the model
        y1 = mean_absolute_error(y_test_org.iloc[:,0],CE2_df.iloc[:,0])
        # print(y1*(1e-9))
        y2 = mean_absolute_error(y_test_org.iloc[:,1],CE2_df.iloc[:,1])
        # print(y2*(1e-9))
        y3 = mean_absolute_error(y_test_org.iloc[:,2],CE2_df.iloc[:,2])
        # print(y3*(1e-9))
        y4 = mean_absolute_error(y_test_org.iloc[:,3],CE2_df.iloc[:,3])
        # print(y4)
        print("MAE ERRORS OF THE MODEL : ",y1,y2,y3,y4)
        # PERFORMANCE METRICS of the model
        y1 = np.sqrt(mean_squared_error(y_test_org.iloc[:,0],CE2_df.iloc[:,0]))
        # print(y1*(1e-9))
        y2 = np.sqrt(mean_squared_error(y_test_org.iloc[:,1],CE2_df.iloc[:,1]))
        # print(y2*(1e-9))
        y3 = np.sqrt(mean_squared_error(y_test_org.iloc[:,2],CE2_df.iloc[:,2]))
        # print(y3*(1e-9))
        y4 = np.sqrt(mean_squared_error(y_test_org.iloc[:,3],CE2_df.iloc[:,3]))
        # print(y4)

        #save the model
        # pickle.dump(CE2,open(os.path.join(os.getcwd(),'AVGCustEst.pkl'),'wb'))
        # pickle.dump(train_scalar2,open(os.path.join(os.getcwd(),'CE_TargetScalar.pkl'),'wb'))
        # pickle.dump(train_scalar1,open(os.path.join(os.getcwd(),'CE_FeatureScalar.pkl'),'wb'))
    else:
        print("Finished Jobs hasn't Exceeded the threshold")

