import numpy as np
import pandas as pd
from scipy.special import boxcox1p,inv_boxcox1p
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from keras.models import Sequential
from keras.layers import Dense,Dropout
from keras.optimizers import Adam
from keras.wrappers.scikit_learn import KerasRegressor
from keras.losses import mean_squared_error,mean_absolute_error,huber_loss
from sklearn.base import BaseEstimator, TransformerMixin
import warnings
import time
import pickle
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns',None)


# Different coulmn categories
Numericals = ['app_dataGenerationInterval','constraintAreaMaxX','constraintAreaMaxY','mobility_noOfLocations',
              'mobility_Hosts','mobility_speed','numNodes','app_dataSizeInBytes','forwarding_maximumCacheSize','mobility_nodeId']
Categoricals = ['applicationLayer','forwardingLayer','linkLayer','mobilityType']
Targets = ['peakdiskspaceusedbytes','peakramusedsimbytes','peakramusedresultsbytes','totaljobclocktimesec']


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


class CustomEstimator(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.model1 = KerasRegressor(build_fn=self.base1, epochs=100, batch_size=64, verbose=0)
        self.model2 = KerasRegressor(build_fn=self.base2, epochs=100, batch_size=64, verbose=0)
        self.model3 = KerasRegressor(build_fn=self.base3, epochs=100, batch_size=64, verbose=0)
        self.model4 = KerasRegressor(build_fn=self.base4, epochs=100, batch_size=64, verbose=0)

    # def fit(self,X,y):
    #   history1 = self.model1.fit(X,y[0])
    #   history2 = self.model2.fit(X,y[1])
    #   history3 = self.model3.fit(X,y[2])
    #   history4 = self.model4.fit(X,y[3])
    def fit(self, X, y, x_val_scaled, y_val_scaled):
        history1 = self.model1.fit(X, y[0], validation_data=(x_val_scaled, y_val_scaled))
        history2 = self.model2.fit(X, y[1], validation_data=(x_val_scaled, y_val_scaled))
        history3 = self.model3.fit(X, y[2], validation_data=(x_val_scaled, y_val_scaled))
        history4 = self.model4.fit(X, y[3], validation_data=(x_val_scaled, y_val_scaled))
        return self, [history1, history2, history3, history4]

    def predict(self, x_test):
        p1 = pd.DataFrame(self.model1.predict(x_test))
        p2 = pd.DataFrame(self.model2.predict(x_test))
        p3 = pd.DataFrame(self.model3.predict(x_test))
        p4 = pd.DataFrame(self.model4.predict(x_test))
        pred_df = pd.concat([p1, p2, p3, p4], axis=1)

        return pred_df

    def base1(self):
        model1 = Sequential()
        model1.add(Dense(units=44, input_dim=x_train_scaled.shape[1], activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(22, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(12, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(8, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(4, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(1))
        model1.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=0.01), metrics=['mean_squared_error'])
        return model1

    def base2(self):
        model2 = Sequential()
        model2.add(Dense(units=44, input_dim=x_train_scaled.shape[1], activation='relu'))
        model2.add(Dropout(0.1))
        model2.add(Dense(22, activation='relu'))
        model2.add(Dropout(0.1))
        model2.add(Dense(12, activation='relu'))
        model2.add(Dropout(0.1))
        model2.add(Dense(8, activation='relu'))
        model2.add(Dropout(0.1))
        model2.add(Dense(4, activation='relu'))
        model2.add(Dropout(0.1))
        model2.add(Dense(1))
        model2.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=0.01), metrics=['mean_squared_error'])
        return model2

    def base3(self):
        model3 = Sequential()
        model3.add(Dense(units=44, input_dim=x_train_scaled.shape[1], activation='relu'))
        model3.add(Dropout(0.1))
        model3.add(Dense(22, activation='relu'))
        model3.add(Dropout(0.1))
        model3.add(Dense(12, activation='relu'))
        model3.add(Dropout(0.1))
        model3.add(Dense(8, activation='relu'))
        model3.add(Dropout(0.1))
        model3.add(Dense(4, activation='relu'))
        # model3.add(Dropout(0.1))
        model3.add(Dense(1))
        model3.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=0.01), metrics=['mean_squared_error'])
        return model3

    def base4(self):
        model4 = Sequential()
        model4.add(Dense(units=44, input_dim=x_train_scaled.shape[1], activation='relu'))
        model4.add(Dropout(0.1))
        model4.add(Dense(22, activation='relu'))
        model4.add(Dropout(0.1))
        model4.add(Dense(12, activation='relu'))
        model4.add(Dropout(0.1))
        model4.add(Dense(8, activation='relu'))
        model4.add(Dropout(0.1))
        model4.add(Dense(4, activation='relu'))
        model4.add(Dropout(0.1))
        model4.add(Dense(1))
        model4.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=0.01), metrics=['mean_squared_error'])
        return model4

CE = CustomEstimator()
start_time = time.time()
# _ , histories = CE.fit(x_train_scaled,[y_train_scaled.iloc[:,0].values,y_train_scaled.iloc[:,1].values,y_train_scaled.iloc[:,2].values,y_train_scaled.iloc[:,3].values])
_ , histories = CE.fit(x_train_scaled,[y_train_scaled.iloc[:,0].values,y_train_scaled.iloc[:,1].values,y_train_scaled.iloc[:,2].values,y_train_scaled.iloc[:,3].values],x_val_scaled,y_val_scaled)
end_time = time.time()
print(end_time-start_time)

train_loss = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(pd.DataFrame(np.hstack((np.array(histories[0].history['loss']).reshape(-1,1),np.array(histories[1].history['loss']).reshape(-1,1),np.array(histories[2].history['loss']).reshape(-1,1),np.array(histories[3].history['loss']).reshape(-1,1))))),0.20)).multiply(1e-9)
val_loss = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(pd.DataFrame(np.hstack((np.array(histories[0].history['val_loss']).reshape(-1,1),np.array(histories[1].history['val_loss']).reshape(-1,1),np.array(histories[2].history['val_loss']).reshape(-1,1),np.array(histories[3].history['val_loss']).reshape(-1,1))))),0.20)).multiply(1e-9)

train_loss_time = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(pd.DataFrame(np.hstack((np.array(histories[0].history['loss']).reshape(-1,1),np.array(histories[1].history['loss']).reshape(-1,1),np.array(histories[2].history['loss']).reshape(-1,1),np.array(histories[3].history['loss']).reshape(-1,1))))),0.20))
val_loss_time = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(pd.DataFrame(np.hstack((np.array(histories[0].history['val_loss']).reshape(-1,1),np.array(histories[1].history['val_loss']).reshape(-1,1),np.array(histories[2].history['val_loss']).reshape(-1,1),np.array(histories[3].history['val_loss']).reshape(-1,1))))),0.20))


#Inferences
x = CE.predict(x_test_scaled)
CE_df = pd.DataFrame(inv_boxcox1p(train_scalar2.inverse_transform(x),0.20),columns=y_test_scaled.columns,index=y_test_scaled.index)
y_test_org  = inv_boxcox1p(y_test,0.20)

# PERFORMANCE METRICS of the model
y1 = mean_absolute_error(y_test_org.iloc[:,0],CE_df.iloc[:,0])
print(y1*(1e-9))
y2 = mean_absolute_error(y_test_org.iloc[:,1],CE_df.iloc[:,1])
print(y2*(1e-9))
y3 = mean_absolute_error(y_test_org.iloc[:,2],CE_df.iloc[:,2])
print(y3*(1e-9))
y4 = mean_absolute_error(y_test_org.iloc[:,3],CE_df.iloc[:,3])
print(y4)

# PERFORMANCE METRICS of the model
y1 = np.sqrt(mean_squared_error(y_test_org.iloc[:,0],CE_df.iloc[:,0]))
print(y1*(1e-9))
y2 = np.sqrt(mean_squared_error(y_test_org.iloc[:,1],CE_df.iloc[:,1]))
print(y2*(1e-9))
y3 = np.sqrt(mean_squared_error(y_test_org.iloc[:,2],CE_df.iloc[:,2]))
print(y3*(1e-9))
y4 = np.sqrt(mean_squared_error(y_test_org.iloc[:,3],CE_df.iloc[:,3]))
print(y4)


#Save the  model
# pickle.dump(CE,open('NNCustEst.pkl','wb'))
# pickle.dump(train_scalar2,open('CE_TargetScalar.pkl','wb'))
# pickle.dump(train_scalar1,open('CE_FeatureScalar.pkl','wb'))

# Epoch vs Loss Plots for Target Variables

plt.rcParams["figure.figsize"] = (20,10)
fig,axs = plt.subplots(2,2)

axs[0,0].plot(train_loss.iloc[:,0])
axs[0,0].plot(val_loss.iloc[:,0])
axs[0,0].set_title('Peak Disk Usage')
axs[0,0].set_xlabel('epochs')
axs[0,0].set_ylabel('MSE Loss in GB')
axs[0,0].legend(['train', 'val'], loc='upper left')

axs[0,1].plot(train_loss.iloc[:,1])
axs[0,1].plot(val_loss.iloc[:,1])
axs[0,1].set_title('Peak Simulation RAM')
axs[0,1].set_xlabel('epochs')
axs[0,1].set_ylabel('MSE Loss in GB')
axs[0,1].legend(['train', 'val'], loc='upper left')

axs[1,0].plot(train_loss.iloc[:,2])
axs[1,0].plot(val_loss.iloc[:,2])
axs[1,0].set_title('Peak Results Parsing RAM')
axs[1,0].set_xlabel('epochs')
axs[1,0].set_ylabel('MSE Loss in GB')
axs[1,0].legend(['train', 'val'], loc='upper left')

axs[1,1].plot(train_loss_time.iloc[:,3])
axs[1,1].plot(val_loss_time.iloc[:,3])
axs[1,1].set_title('Total Time Taken')
axs[1,1].set_xlabel('epochs')
axs[1,1].set_ylabel('MSE Loss in Secs')
axs[1,1].legend(['train', 'val'], loc='upper left')

# plt.set_title('Training/Validation plots')
fig.show()