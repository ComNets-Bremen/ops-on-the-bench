import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import skew
from scipy.special import boxcox1p


# PASS THE INPUT DATASET extracted from the 'DataExtraction.py' with name 'fifth'
# print(fifth.columns)

sns.histplot(fifth['mobility_nodeId'],stat='count')

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