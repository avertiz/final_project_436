# Packages
import pandas as pd
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

############################################################
################### Connect to Postgres ####################
###################### and get data ########################
############################################################

# Connect
connection = psycopg2.connect(
    host = [INSERT],
    port = '5432',
    user = [INSERT],
    password = [INSERT],
    dbname=[INSERT]
            )

# Get the whole table
df = pd.read_sql("""SELECT * FROM listings """, connection)

############################################################
################### Cleaning the data ######################
############################################################

# Get rid of bad prices and locations
data =  df.loc[(df.price > 100) & 
(df.square_feet < 4000) &
(df.latitude > 30) &
(df.longitude < -80) &
(df.bedrooms <= 4) &
(df.distance_from_city_center < 20)]

# Reduce number of features
data = data[['price', \
'has_image', \
'bedrooms', \
'square_feet', \
'distance_from_city_center', \
# 'price_per_sqft', \
'zip']] 

# Get rid of mising data
data = data.dropna()

############################################################
##################### Preprocessing ########################
############################################################

# One-hot encode has_image feature
data = pd.concat([data, pd.get_dummies(data['has_image'], prefix='has_image')],
axis = 1)

data.drop(['has_image'], axis=1, inplace=True)

# One-hot encode zip feature
data = pd.concat([data, pd.get_dummies(data['zip'], prefix='zip')],
axis = 1)

data.drop(['zip'], axis=1, inplace=True)

# Features and labels
X = np.array(data.iloc[:, 1:])
y = np.array(data['price'])

# Train test split
X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size= 0.2)

############################################################
######################### Model ############################
############################################################

# LinearRegression
lr_pipe = Pipeline([('lr', LinearRegression())])

lr_pipe.fit(X_train, y_train)
lr_pipe.score(X_test, y_test)
lr_predictions = lr_pipe.predict(X_test)

# GradientBoostingRegressor
gbr_pipe = Pipeline([('scaler', StandardScaler()), 
                    ('gbr', GradientBoostingRegressor())])

gbr_pipe.fit(X_train, y_train)
gbr_pipe.score(X_test, y_test)
gbr_predictions = gbr_pipe.predict(X_test)

# Take a look at results
compare = [[a, b, c] for a, b, c in zip(y_test, lr_predictions, gbr_predictions)]

compare_df = pd.DataFrame(compare, columns = ['test','lr_predictions', 'gbr_predictions'])

compare_df = compare_df.sort_values('test').reset_index(drop=True)

compare_df['index_col'] = compare_df.index

ax = plt.gca()
compare_df.plot(kind='scatter',x='index_col',y='test',ax=ax)
compare_df.plot(kind='line',x='index_col',y='lr_predictions', color='blue',ax=ax)
compare_df.plot(kind='line',x='index_col',y='gbr_predictions', color='red',ax=ax)

plt.show()
