import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin,RegressorMixin,clone
import warnings
warnings.filterwarnings('ignore')


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
