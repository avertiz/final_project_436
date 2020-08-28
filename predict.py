import pandas as pd
import numpy as np
import pickle
import argparse

# takes inputs and returns a predicted listing price
def predict(model_file, column_file, square_feet, distance_from_city_center, has_image, bedrooms, zip_code):    

    # load column names for model
    data = pd.read_csv(column_file)

    # Fixing data dtypes
    for col in data:
        data[col] = data[col].astype('float')

    ###### add inputs #####

    # square_feet
    data['square_feet'] = [float(square_feet)]
    # distance_from_city_center
    data['distance_from_city_center'] = float(distance_from_city_center)
    if has_image:
        data['has_image_True'] = 1
    else:
        data['has_image_False'] = 1
    # bedrooms and zip code
    for col in data:
        if len(col) >= 10:
            if col[9] == bedrooms:
                data[col] = 1
            if col[4:9] == zip_code:
                data[col] = 1
    # making everything else 0
    for col in data:
        if data[col].isnull().values.any():
            data[col] = 0

    ###### model prep #####
    X = np.array(data.iloc[:, 1:])

    # load model
    model = pickle.load(open(model_file, 'rb'))

    # Predict
    prediction = model.predict(X)
    print('List this unit for: $', round(prediction[0]))

# Main function
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-mf", "--modelfile_name", help= "SAV file that has the model")
    parser.add_argument("-c", "--cols", help= "The columns file ")
    parser.add_argument("-sf", "--square_ft", help= "Square ft of unit to list")
    parser.add_argument("-d", "--dist_from_dt", help= "unit's distance from city center")
    parser.add_argument("-b", "--beds", help= "unit's number of bedrooms")
    parser.add_argument("-p", "--has_pics", help= "Does the unit have pictures?")
    parser.add_argument("-z", "--zip", help= "unit's zip code")
    args = parser.parse_args()

    modelfile_name = args.modelfile_name
    cols = args.cols
    square_ft = args.square_ft
    dist_from_dt = args.dist_from_dt
    has_pics = args.has_pics
    beds = args.beds
    zip_ = args.zip

    predict(model_file = modelfile_name,
    column_file = cols, 
    square_feet = square_ft, 
    distance_from_city_center = dist_from_dt,
    has_image = has_pics,
    bedrooms = beds, 
    zip_code = zip_)

# CLI
if __name__ == '__main__':
    main()
