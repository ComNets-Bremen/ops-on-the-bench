from django.shortcuts import render
# from django.core.files import File
from django.conf import settings 
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from pathlib import Path
import os
import pickle
import re
import numpy as np
# import keras
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score,mean_squared_error,mean_absolute_error,mean_absolute_percentage_error
from keras.models import Sequential
from keras.layers import Dense,BatchNormalization,Dropout
from keras.optimizers import Adam,SGD,RMSprop,Adadelta,Adagrad,Adamax,Nadam,Ftrl
from keras.callbacks import EarlyStopping,ModelCheckpoint
from keras.wrappers.scikit_learn import KerasClassifier,KerasRegressor
from math import floor
from sklearn.metrics import make_scorer,accuracy_score
from sklearn.model_selection import StratifiedKFold,KFold
from keras.layers import LeakyReLU
from scipy import stats
from scipy.stats import norm, skew, johnsonsu, lognorm
from scipy.special import boxcox1p,inv_boxcox1p
from sklearn.ensemble import RandomForestRegressor,  GradientBoostingRegressor
from sklearn.base import BaseEstimator, TransformerMixin,RegressorMixin,clone
LeakyReLU = LeakyReLU(alpha=0.1)
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns',None)
from joblib import load
from sklearn.multioutput import MultiOutputRegressor


BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_ROOT = os.path.join(BASE_DIR,'media')



# Create your views here.
def fileUp(request):
    return render(request,"OOTBHome.html")

def upload(request):
    if request.method == 'POST':
        file = request.FILES.get('file',None)
        if file is None:
            return HttpResponse("Nothings FOUND")
        # fs = FileSystemStorage()
        # runconfig = 'Config Herald-1s-Epidemic-750-nodes-SWIM'
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        # filenames.append(filename)
        uploaded_file_url = fs.url(filename)
        file_path = os.path.join(MEDIA_ROOT, filename)
        with open(file_path,'r') as f:
            filecontent = f.read().splitlines()
        omnetl = ''.join([line for line in filecontent if not line.startswith('#')])
        runs = re.findall(r'\[([0-9a-zA-Z\-\s]+)\]',omnetl)
        # settings.OMNET = omnetl
        request.session['omnet'] = omnetl
        return render(request,"runConfig.html",{"runs":runs})

    

def local_html(request):
    return render(request,"OOTBUpload.html")

def local_html2(request):
    return render(request,"Final.html")
    # return HttpResponse(keras.backend.backend())

def predict(request):
    if request.method == 'POST':
        runConfig = request.POST.get('option')
        if runConfig is None:
            return HttpResponse("Nothings FOUND")
        # return HttpResponse(runConfig)

        # runconfig = 'Config Herald-1s-Epidemic-750-nodes-SWIM'
        runconfig = runConfig
        # if runconfig==runConfig:
        #     boo = "Same"
        # else:
        #     boo = "different"
        omnet = request.session.get('omnet')
        omnet = re.compile(runconfig + r'[\]\n\#\s\w\*\.=\(\)\"\,\-\/]+').findall(omnet)
        allParams = re.findall(r'\*\*\.([a-zA-Z\.]+) = ([A-Za-z0-9\"\.\/\-]+)',str(omnet))
        dictParams = dict(allParams)
        df1 = pd.DataFrame(dictParams,index=[0])
        df1.columns = df1.columns.str.replace('.','_',regex=False)
        Numericals = ['app_dataGenerationInterval','constraintAreaMaxX','constraintAreaMaxY','mobility_noOfLocations','mobility_Hosts',
                      'mobility_speed','numNodes','app_dataSizeInBytes','forwarding_maximumCacheSize']
        Categoricals = ['applicationLayer','forwardingLayer','linkLayer','mobilityType']
        df = pd.concat([df1[Numericals],df1[Categoricals]],axis=1)
        df = df.fillna('0')
        fwd = []
        app = []
        mob = []
        link = []
        Id = []
        
        if df['forwardingLayer'].values[0].replace('"','') == "KEpidemicRoutingLayer":
            fwd = [0,0,0,0,0]
        elif df['forwardingLayer'].values[0].replace('"','') == "KKeetchiLayer":
            fwd = [1,0,0,0,0]
        elif df['forwardingLayer'].values[0].replace('"','') == "KOptimumDelayRoutingLayer":
            fwd = [0,1,0,0,0]
        elif df['forwardingLayer'].values[0].replace('"','') == "KProphetRoutingLayer":
            fwd = [0,0,1,0,0]
        elif df['forwardingLayer'].values[0].replace('"','') == "KRRSLayer":
            fwd = [0,0,0,1,0]
        # elif df['forwardingLayer'].values[0] == "KSpraywaitRoutingLayer":
        else:
            fwd = [0,0,0,0,1]
        
        if df['mobilityType'].values[0].replace('"','') =="BonnMotionMobility":
            mob = [0,0]
        elif df['mobilityType'].values[0].replace('"','') =="SWIMMobility":
            mob = [1,0]
        else:
            mob = [0,1]
            
        if df['applicationLayer'].values[0].replace('"','') =="KHeraldApp":
            app = [0,0]
        elif df['applicationLayer'].values[0].replace('"','') =="KHeraldAppForDifferentiatedTraffic":
            app = [1,0]
        else:
            app = [0,1]
            
        if df['linkLayer'].values[0].replace('"','') =="KWirelessInterface":
            link = [0]
        else:
            link = [1]
            
        if 'mobility_nodeId' in dictParams:
            Id = [1]
        else:
            Id = [0]
        
        
    
        df['app_dataGenerationInterval'] =  df.app_dataGenerationInterval.apply(lambda x : x.replace('s','') if 's' in x else x)
        df['constraintAreaMaxX'] =  df.constraintAreaMaxX.apply(lambda x : x.replace('m','') if 'm' in x else x)
        df['constraintAreaMaxY'] =  df.constraintAreaMaxY.apply(lambda x : x.replace('m','') if 'm' in x else x)
        df['mobility_speed'] =  df.mobility_speed.apply(lambda x : x.replace('mps','') if 'mps' in x else x)
        
        def for_maxCache(cache):
            if 'bytes' in cache:
                return cache.replace('bytes','')
            elif 'byte' in cache:
                return cache.replace('byte','')
            else:
                return cache
        df['forwarding_maximumCacheSize'] =  df.forwarding_maximumCacheSize.apply(lambda x : for_maxCache(x))
        
        df_list = df[Numericals].apply(pd.to_numeric).values
        
        input = np.concatenate([df_list,np.array([Id + app + fwd + link + mob])],axis=1)
        input_df = pd.DataFrame(input)
        bc_input = boxcox1p(input_df,0.20)
        
        fs = open(r'OOTB\pickles\AveragingRegressor\CharmEstFeatureScalar.pkl','rb')
        fscalar = pickle.load(fs)
        fs.close()
        
        scaled_input = fscalar.transform(bc_input)
        
        mod1 = open(r'OOTB\pickles\AveragingRegressor\CharmAvgReg.pkl','rb')
        model1 = pickle.load(mod1)
        mod1.close()
        
        # mod1 = open(r'OOTB\pickles\NeuralNetworkRegressor\NeuralNetCustomEst.pkl','rb')
        # model1 = pickle.load(mod1)
        # mod1.close()
        # model1 = load('OOTB\testJoblib.pkl')
        
        ts = open(r'OOTB\pickles\AveragingRegressor\CharmEstTargetScalar.pkl','rb')
        tscalar = pickle.load(ts)
        ts.close()
        
        # ONLY FOR NeuralNet Prediction
        # scaled_input = pd.concat([pd.DataFrame(scaled_input.values),pd.DataFrame(scaled_input.values)],axis=0) 
        
        # Averaging Regressor
        predictions = model1.predict(scaled_input)
        
        predictions = tscalar.inverse_transform(pd.DataFrame(predictions).transpose())
        
        # ONLY FOR NeuralNet Prediction
        # predictions = tscalar.inverse_transform(predictions)
        
        
        predictions = np.squeeze(inv_boxcox1p(predictions,0.20))
        
        return render(request,"predict.html",{'result1':round(predictions[0]*1e-9,2),
                                             'result2':round(predictions[1]*1e-9,2),
                                             'result3':round(predictions[2]*1e-9,2),
                                             'result4':round(predictions[3],2)})
        # return HttpResponse(len(predictions))