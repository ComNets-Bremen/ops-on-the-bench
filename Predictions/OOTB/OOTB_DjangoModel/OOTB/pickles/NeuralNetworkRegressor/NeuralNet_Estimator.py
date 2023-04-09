from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.base import BaseEstimator, TransformerMixin
import pandas as pd
from keras.models import Sequential
from keras.layers import Dense,Dropout
from keras.optimizers import Adam

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
        model1.add(Dense(units=44, input_dim=20, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(22, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(12, activation='relu'))
        model1.add(Dropout(0.2))
        model1.add(Dense(8, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(4, activation='relu'))
        model1.add(Dropout(0.1))
        model1.add(Dense(1))
        model1.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=0.01), metrics=['mean_squared_error'])
        return model1

    def base2(self):
        model2 = Sequential()
        model2.add(Dense(units=44, input_dim=20, activation='relu'))
        model2.add(Dropout(0.2))
        model2.add(Dense(22, activation='relu'))
        model2.add(Dropout(0.2))
        model2.add(Dense(12, activation='relu'))
        model2.add(Dropout(0.2))
        model2.add(Dense(8, activation='relu'))
        model2.add(Dropout(0.2))
        model2.add(Dense(4, activation='relu'))
        model2.add(Dropout(0.1))
        model2.add(Dense(1))
        model2.compile(loss='mean_squared_error', optimizer=Adam(learning_rate=0.01), metrics=['mean_squared_error'])
        return model2

    def base3(self):
        model3 = Sequential()
        model3.add(Dense(units=44, input_dim=20, activation='relu'))
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
        model4.add(Dense(units=44, input_dim=20, activation='relu'))
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