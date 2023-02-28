# Predicting the Resources of Network Simulations

This is the repository for the 'Predicting the Resources of Network Simulations' project. This project is developed as a Student Master Thesis by the department of sustainable communication networks, University of Bremen, Germany.

 - [comnets.uni-bremen.de](https://www.uni-bremen.de/comnets)
 - [ComNets @Twitter](https://twitter.com/ComNetsBremen)
 - [ComNets @Youtube](https://www.youtube.com/c/ComNetsBremen)

## Abstract
The OOTB platform uses containerization techniques to run several simulations in parallel where each simulation takes some amount of available resources and time to complete. It is important to identify or halt simulations that take longer durations and more resources to complete than usual as they hinder performing parallel simulations.

This project provides a solution to overcome this problem by training a Machine learning model and using it to predict the resources prior to the simulation and give an estimate to the user about the network resource utilization.

## Methodology
**Steps**

- Install all the necessary dependencies
- Run Simulations on OOTB to generate data
- Extraction of data
- Data Cleaning and Preprocessing
- Model Building and Inference
- Pickling Model instances
- Unpickling the model instance in OOTB Django environment

**Install**

This project requires **Python** and the following Python libraries installed:
- [NumPy](http://www.numpy.org/)
- [Pandas](http://pandas.pydata.org/)
- [TensorFlow](https://pypi.org/project/tensorflow/)
- [scikit-learn](http://scikit-learn.org/stable/)
- [XGBoost](https://pypi.org/project/xgboost/)
- [Keras](https://pypi.org/project/keras/)
- [lightGBM](https://pypi.org/project/lightgbm/)
- [pickle](https://pypi.org/project/pickle5/)
- [Django](https://pypi.org/project/Django/)

All the required dependencies can found here.

You will also need to have software installed to run and execute a [Jupyter Notebook](http://jupyter.org/install.html).
If you do not have Python installed yet, it is highly recommended that you run and execute on [Google Colab](https://colab.research.google.com/), which already has most of the above packages included already.

**Data**

The data used for building the model in this project is obtained by performing simulations on OOTB tool. Once the required number of simulations are performed the user can also get these simulation results from the ‘Collect Simulation Data’ tab in the OOTB in JSON format. And the required data related to the simulation parameters can be extracted using the [JSONExtraction.ipynb](https://colab.research.google.com/github/Srikanth635/COMNETS/blob/main/Source_Code/JSONExtraction.ipynb)

The dataset used for the training the models in this project is available in the root/[Dataset](https://github.com/Srikanth635/COMNETS/tree/main/Dataset) folder

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
 
 **Targets**
 - Peak Disk Usage
 - Peak RAM Used in Simulation
 - Peak RAM Used in Results parsing
 - Total Job Time Taken
 
**Models**

 **Averaging Regressor**
 
 This is a custom estimator model thath utilizes three different regression algorithms and averages their outcomes. This results in better stability and perfromance of the model in situations of smaller dataset. The three differnt algorithms used in this custom estimator are Gradient Boost Regressor, lightGBM regressor and XGBoost regressor.
 
Gradient Boosting Regressor is a type of machine learning model used for regression problems. It is an ensemble learning algorithm that combines multiple weak models to create a strong predictive model. The main idea behind Gradient Boosting is to fit a regression model to the residuals of the previous model. This way, each new tree corrects the errors of the previous ones, leading to a more accurate model. It is a popular algorithm due to its high predictive accuracy and robustness to outliers.

LightGBM is a gradient boosting framework that uses a tree-based learning algorithm. It is similar to other gradient boosting algorithms such as XGBoost and Gradient Boosting Regressor, but it uses a novel technique called Gradient-based One-Side Sampling (GOSS) to speed up the training process. In LightGBM, each tree is built on the previous tree's residuals. However, instead of using all the data, GOSS selects only a subset of the data based on the gradient magnitude, which reduces the number of data points used for training. This technique helps to improve the efficiency of the training process without sacrificing the model's accuracy.

[XGBoost (Extreme Gradient Boosting)](https://xgboost.readthedocs.io/en/stable/index.html) is a popular gradient boosting algorithm with an efficient and scalable implementation of the gradient boosting framework. XGBoost includes L1 and L2 regularization to control the model's complexity and prevent overfitting. XGBoost works by sequentially adding decision trees to the model while minimizing the objective function, which is the sum of the loss function and a regularization term. The loss function measures the difference between the predicted values and the actual values, while the regularization term controls the complexity of the model to prevent overfitting.

**Dense Neural Network**

A dense neural network is a type of artificial neural network that consists of multiple layers of densely connected neurons. Dense neural networks are commonly used for regression tasks and can be used to model complex non-linear relationships between input variables and output variables. Some of the hyperparameters that can be tuned in a dense neural network for regression include the number of layers, the number of neurons per layer, the activation functions, the learning rate, the batch size, and the number of epochs. During the training process, the neural network learns to adjust the weights and biases of the neurons to minimize the loss function, which measures the difference between the predicted values and the actual values. The optimizer is used to update the weights and biases in each iteration of the training process.

**Run**

Once after the dataset is built we perform one-hot encoding for the categorical features. Then the data is transformed accordingly to reduce the skewness in the independent and dependent variables, many transformation techniques like boxcox, sqrt, log, lognorm etc., are available and finally we perform standardization to bring the features under same scale and center their mean values. Both the models can be executed through the colab links provided in the respective models in the root/[Source_Code](https://github.com/Srikanth635/COMNETS/tree/main/Source_Code)  folder.

All the evaluation graphs and results are available in root/[Results/Evaluation Graphs](https://github.com/Srikanth635/COMNETS/tree/main/Results/Evalaution%20Graphs) folder

**Save the Model**

Once the model is finished training, the model instance and the standard scalar instances are saved in pickle format using python's [pickle](https://docs.python.org/3/library/pickle.html) library.

**Django**

OOTB uses the containerisation mechanism offered by Docker to host Linux based instances of the OPS and OMNeT++. These Docker instances are brought up in the backend of OOTB on an as-needed basis, based on the simulations initiated by users using the front-end of OOTB. OOTB uses the Django Framework to build the system required to obtain simulations request of users to channel them to worker processes in the backend that running the Docker containers.

Django is a high-level open-source web framework written in Python. It follows the model-view-controller (MVC) architectural pattern. Django provides a collection of tools and libraries that make it easier to build web applications quickly and efficiently. Django provides built-in tools for managing user authentication and authorization, making it easy to secure your web application. Django comes with a built-in administration site that allows you to manage your application's data through a web-based interface.

**Model Deployment in Django Environment**

The sample local build of OOTB in Django can be found here. All the necessary templates are linked to allow the user to upload the configuration file and trigger the model to predict the resources required by the simulation of the uploaded configuration.

The instances of models and scaling functions are unpickled using the Python's pickle in the Django views.py file, as can be seen here and are used to predict the target resources. As the trained models are custom estimators, their implementation is added to the Django in the manage.py file before the main method as can be seen here. This makes the Django aware to create instances of these custom estimators.

**Project Summary**

In this work, we've taken few of the simulations parameters i.e., 10 as features for predicitng 4 target variables. And the range of values for the parameter 'NumNodes' are from 10 to 1000. Considering the variablity and size of the dataset available we went with tree based algorithms for building the predictive models and the results obtained were satisfactory inspite of having some imbalances in the dataset.

## Future Scope

The work can be extended by incorporating more parameters as features and implementing through complex models like neural networks. The size of dataset can be increased which helps in figuring out more complex patterns in the data.