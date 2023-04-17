# Predicting the Resources of Network Simulations

This is the repository for the 'Predicting the Resources of Network Simulations' project. This project is developed as a Student Master Thesis by the department of sustainable communication networks, University of Bremen, Germany.

 - [comnets.uni-bremen.de](https://www.uni-bremen.de/comnets)
 - [ComNets @Twitter](https://twitter.com/ComNetsBremen)
 - [ComNets @Youtube](https://www.youtube.com/c/ComNetsBremen)

## Abstract
The OOTB platform uses containerization techniques to run several simulations in parallel where each simulation takes some amount of available resources and time to complete. It is important to identify or halt simulations that take longer durations and more resources to complete than usual as they hinder performing parallel simulations.

This project provides a solution to overcome this problem by training a Machine learning model and using it to predict the resources prior to the simulation and give an estimate to the user about the network resource utilization.

## Methodology
**Procedure**

- Install all the necessary dependencies
- Run Simulations on OOTB to generate data
- Extraction of data
- Data Cleaning and Preprocessing
- Model Building and Inference
- Pickling Model instances
- Unpickling the model instance in OOTB Django environment
- Enabling Cronjob to execute new queue mechanism

**Install**

This project requires **Python** and the following Python libraries installed:
- [NumPy](http://www.numpy.org/)
- [Pandas](http://pandas.pydata.org/)
- [scikit-learn](http://scikit-learn.org/stable/)
- [XGBoost](https://pypi.org/project/xgboost/)
- [pickle](https://pypi.org/project/pickle5/)
- [Django](https://pypi.org/project/Django/)
- [Requests](https://requests.readthedocs.io/en/latest/)
- [JSON](https://docs.python.org/3/library/json.html)
- [rq](https://python-rq.org/)

All the required dependencies can found [here](./model/requirements.txt).

You will also need to have software installed to run and execute a [Jupyter Notebook](http://jupyter.org/install.html).
If you do not have Python installed yet, it is highly recommended that you run and execute on [Google Colab](https://colab.research.google.com/), which already has most of the above packages included already.

**Data Generation**

The data used for building the model in this project is obtained by performing simulations on OOTB tool. Once the required number of simulations are performed the user can also get these simulation results from the ‘Collect Simulation Data’ tab in the OOTB in JSON format. And the required data related to the simulation parameters can be extracted using the [DataExtraction.py](./model/Source code/DataExtraction.py)

The dataset used for the training the models in this project is available in the [Dataset.csv](./model/Dataset/Dataset.csv) folder and the preprocessing steps performed on the dataset is availble at [DataPreProcessing.py](./OOTB/SourceCode/Data_PreProcessing.py)

**Features**

 - Number of Nodes
 - Data Generation Interval
 - Data Size in bytes
 - Constraint Area X
 - Constraint Area Y
 - Locations
 - Hosts
 - Maximum Cache Size
 - Forwarding Layer
 - Application Layer
 - Mobility Speed
 
 **Targets**
 - Peak Disk Usage
 - Peak RAM Used in Simulation
 - Peak RAM Used in Results parsing
 - Total Job Time Taken
 
**Predictive Models**

 **[Averaging Regressor](./model/Source code/Model_AveragingRegressor.py)**
 
 This is a custom estimator model thath utilizes three different regression algorithms and averages their outcomes. This results in better stability and perfromance of the model in situations of smaller dataset. The three differnt algorithms used in this custom estimator are Gradient Boost Regressor, Random Forest regressor and XGBoost regressor.
 
[Gradient Boosting Regressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.GradientBoostingRegressor.html) is a type of machine learning model used for regression problems. It is an ensemble learning algorithm that combines multiple weak models to create a strong predictive model. The main idea behind Gradient Boosting is to fit a regression model to the residuals of the previous model. This way, each new tree corrects the errors of the previous ones, leading to a more accurate model. It is a popular algorithm due to its high predictive accuracy and robustness to outliers.

[Random Forest Regressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html) A random forest regressor is a type of machine learning algorithm that is used for regression problems.In a random forest regressor, the input data is divided into multiple random subsets, and a decision tree is constructed for each subset. Each decision tree is trained on a different subset of the data, and the prediction of the model is obtained by aggregating the predictions of all the individual decision trees.The random forest algorithm uses two sources of randomness: the random subsets used to train each decision tree and the random selection of features used at each split in the decision tree. These sources of randomness help to reduce overfitting and improve the generalization performance of the model.

[XGBoost (Extreme Gradient Boosting)](https://xgboost.readthedocs.io/en/stable/index.html) is a popular gradient boosting algorithm with an efficient and scalable implementation of the gradient boosting framework. XGBoost includes L1 and L2 regularization to control the model's complexity and prevent overfitting. XGBoost works by sequentially adding decision trees to the model while minimizing the objective function, which is the sum of the loss function and a regularization term. The loss function measures the difference between the predicted values and the actual values, while the regularization term controls the complexity of the model to prevent overfitting.


**Run (Inference)**

Once after the dataset is built we perform one-hot encoding for the categorical features. Then the data is transformed accordingly to reduce the skewness in the independent and dependent variables, many transformation techniques like boxcox, sqrt, log, lognorm etc., are available and finally the data is standardized to bring the features under same scale and center their mean values.

**Save the Model**

Once the model is finished training, the model instance and the standard scalar instances are saved in pickle format using python's [pickle](https://docs.python.org/3/library/pickle.html) library.

**Django**

OOTB uses the containerisation mechanism offered by Docker to host Linux based instances of the OPS and OMNeT++. These Docker instances are brought up in the backend of OOTB on an as-needed basis, based on the simulations initiated by users using the front-end of OOTB. OOTB uses the Django Framework to build the system required to obtain simulations request of users to channel them to worker processes in the backend that running the Docker containers.

[Django](https://www.djangoproject.com/) is a high-level open-source web framework written in Python. It follows the model-view-controller (MVC) architectural pattern. Django provides a collection of tools and libraries that make it easier to build web applications quickly and efficiently. Django provides built-in tools for managing user authentication and authorization, making it easy to secure your web application. Django comes with a built-in administration site that allows you to manage your application's data through a web-based interface.

**Model Deployment in Django Environment**

Respective changes are made to views.py in the [NewSimWizard](./manager/omnetppManager/views.py#L573) class by adding a predict a method that takes in the uploaded configuration file and the selected run configuration. Then parsing of the configuration file to extract required parameters is done and predictions are displayed. To display the predicted results of the simulation minor chnages were made to the exisitng template by creating a form as a the third step. Also the prediction values get saved in the sqlite simulation model as four different fields are added as shown [here](./manager/omnetppManager/models.py#L140)

The instances of models and scaling functions are unpickled using the Python's pickle in the Django views.py file, as can be seen [here](./manager/omnetppManager/views.py#L790) and are used to predict the target resources. As the trained models are custom estimators, their implementation is added to the Django in the manage.py file before the main method as can be seen [here](./manager/manage.py#L21). This makes the Django aware of this to create instances of these custom estimators.

**Enabling Cronjob to Update Redis Queue**

For the purpose of having an efficient mechanism to handle simulation jobs on redis queue such that simulation will have enough resources on the server required for its execution and gets picked up by the worker on that server. To enable this a python script was written which contains commands to retrieve server resource information, calculate the total resources used by the ongoing simulations and then finds the avaiable respources on the server. Then this information is used to shuffle the redis queue accordingly to keep the next suitable queued job at the front. The procedure followed for these steps can be found in [this](./manager/omnetppManager/queueUpdater.py) Python script. 

Do the following to create the cron job.

  - Edit crontab by running,

   ```bash
   crontab -e
   ```

  - Insert the following entry in the Cron file. /.../ refers to where OOTB is installed.

  ```bash
  * * * * * /.../python3 /.../ops-on-the-bench/manager/omnetppManager/queueUpdater.py
  ```

  The above first `/.../` refers to where Python is installed and the second '/.../' referes to the location of OOTB.
  
**Project Summary**

In this work, we've taken some of the simulations parameters for predicitng 4 target variables. And the range of values for one of the feature parameter 'NumNodes' are from 10 to 3600 that includes simulations with and without trace files i.e., BONN and SWIM mobility simulations. Considering the variablity and size of the dataset available, a stacking regresor model is used which averages the predictions of different tree based algorithms. Also 'queueUpdater.py' script has been executed as a cronjob to shuffel the order of jobs in the redis queue based on their resource requirement.
