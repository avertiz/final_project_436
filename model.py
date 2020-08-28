# Packages
import pandas as pd
import numpy as np
import psycopg2
import matplotlib.pyplot as plt
import pickle
import argparse
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Model function
def model(host_, port_, user_, password_, dbname_):

        ############################################################
        ################### Connect to Postgres ####################
        ###################### and get data ########################
        ############################################################

        # Connect
        connection = psycopg2.connect(
        host = host_,
        port = port_,
        user = user_,
        password = password_,
        dbname= dbname_
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

        # One-hot encode bedrooms feature
        data = pd.concat([data, pd.get_dummies(data['bedrooms'], prefix='bedrooms')],
        axis = 1)

        data.drop(['bedrooms'], axis=1, inplace=True)

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
        
        # GradientBoostingRegressor
        gbr_pipe = Pipeline([('scaler', StandardScaler()), 
                        ('gbr', GradientBoostingRegressor())])

        gbr_pipe.fit(X_train, y_train)
        print('R squared:', gbr_pipe.score(X_test, y_test))
        data.iloc[  :0,:].to_csv('columns.csv', index=False)
        pickle.dump(gbr_pipe, open('model.sav', 'wb'))

# Main function
def main():

        parser = argparse.ArgumentParser()
        parser.add_argument("-rh", "--remote_host", help= "AWS RDS host")
        parser.add_argument("-p", "--port", help= "AWS RDS port")
        parser.add_argument("-u", "--user", help= "AWS RDS user")
        parser.add_argument("-pass", "--password", help= "AWS RDS password")
        parser.add_argument("-db", "--dbname", help= "AWS RDS db name")
        args = parser.parse_args()

        remote_host = args.remote_host
        port = args.port
        user = args.user
        password = args.password
        dbname = args.dbname

        model(host_ = remote_host, 
        port_ = port, 
        user_ = user, 
        password_ = password, 
        dbname_ = dbname)

# CLI
if __name__ == '__main__':
    main()
