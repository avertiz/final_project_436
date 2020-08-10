import pandas as pd
import numpy as np
import io
import psycopg2
import argparse
import sys
import requests
import geopy
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from craigslist import CraigslistHousing
from io import StringIO
from math import sin, cos, sqrt, atan2, radians

# Bedrooms and square feet
def extra_features(site, area, category, sort_by, limit):

    # Sort param dictionary
    sorts = {'newest' : 'date',
            'price_asc' : 'priceasc',
            'price_desc' : 'pricedsc'}

    # Parser function
    def bs(content):
        return BeautifulSoup(content, 'html.parser')

    # Logging function.....not sure if necessary
    def requests_get(*args, **kwargs):
        """
        Retries if a RequestException is raised (could be a connection error or
        a timeout).
        """
        logger = kwargs.pop('logger', None)
        try:
            return requests.get(*args, **kwargs)
        except RequestException as exc:
            if logger:
                logger.warning('Request failed (%s). Retrying ...', exc)
            return requests.get(*args, **kwargs)

    # Initiate lists to store features
    ids = []
    br = []
    ft2 = []

    # Iterate through pages
    for page in range(int(limit/120)):

        # Create URL
        if page == 0:
            url = 'https://' + site + '.craigslist.org/search/' + \
            area + '/' + category + '?sort=' + sorts[sort_by]
        else:
            url = 'https://' + site + '.craigslist.org/search/' + \
            area + '/' + category + '?s=' + str(page*120) + '&sort=' + sorts[sort_by]
        
        # Get Response
        response = requests_get(url)
        soup = bs(response.content)

        # Extract Features
        for item in soup.find_all(attrs={"data-id": True}):
            ids.append(item['data-id'])
        overall_count = 0
        br_count = 0
        ft2_count = 0
        for desc in soup.find_all('span', {'class' : 'result-meta'}):
            overall_count += 1
            for h in desc.find_all('span', {'class' : 'housing'}):               
                text = h.get_text().split()
                for string in text:
                    if 'br' in string:
                        br_count += 1
                        br.append(string[0])
                    elif 'ft2' in string:
                        ft2_count += 1
                        ft2.append(string[:-3])
            if overall_count != br_count:
                br.append(None)
                br_count = overall_count
            if overall_count != ft2_count:
                ft2.append(None)
                ft2_count = overall_count

    dict_ = {'id' : ids, 'bedrooms' : br, 'square_feet' : ft2}
    df = pd.DataFrame(dict_)
    return(df)

# Normal craigslist features
def main_features(site, area, category, sort_by, limit, geotagged):

    # Use Craigslist package
    cl = CraigslistHousing(site= site, area= area, category= category)
    results = cl.get_results(sort_by= sort_by, geotagged= geotagged, limit = limit)

    df = {  'id': [],
            'repost_of': [],
            'name': [],
            'url': [],
            'datetime': [],
            'last_updated': [],
            'price': [],
            'where_': [],
            'has_image': [],
            'latitude': [],
            'longitude':[]
        }

    for result in results:
        df['id'].append(result['id'])
        df['repost_of'].append(result['repost_of'])
        df['name'].append(result['name'])
        df['url'].append(result['url'])
        df['datetime'].append(result['datetime'])
        df['last_updated'].append(result['last_updated'])
        df['price'].append(result['price'][1:])
        df['where_'].append(result['where'])    
        df['has_image'].append(result['has_image'])
        if result['geotag'] == None:
                df['latitude'].append(0.0)
                df['longitude'].append(0.0)
        else:
            df['latitude'].append(result['geotag'][0])
            df['longitude'].append(result['geotag'][1])

    df = pd.DataFrame(df)
    return(df)

# Calculate distance from city center
def calc_distance_from_city_center(data):
    R = 3958.8

    lat1 = data['latitude'].apply(radians)
    lon1 = data['longitude'].apply(radians)
    lat2 = radians(41.882054)
    lon2 = radians(-87.627813)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    distance = []

    for dist in range(int(len(dlon))):
        a = sin(dlat[dist] / 2)**2 + cos(lat1[dist]) * cos(lat2) * sin(dlon[dist] / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance.append(R * c)
    
    data['distance_from_city_center'] = distance
    
    return(data)

# Calculate price per square feet
def price_per_sqft(df):
    df['price_per_sqft'] = pd.to_numeric(df['price']) / pd.to_numeric(df['square_feet'])
    return(df)

# Get zipcodes using geopy
def get_zipcode(df, geolocator, lat_field, lon_field):
    try:
        location = geolocator.reverse((df[lat_field], df[lon_field]))
        if 'postcode' in location.raw['address'].keys():
            zip = location.raw['address']['postcode']
            zip = zip[:5]
            zip = int(zip)
            return zip
        else:
            return None
    except:
        return None

####################################################
######### This is how I created the table ##########
####################################################
# cursor.execute("""CREATE TABLE listings(
#                 id                      bigint,
#                 repost_of               bigint,
#                 name                    text,
#                 url                     text,
#                 datetime                timestamp,
#                 last_updated            timestamp,
#                 price                   float,
#                 where_                  text,
#                 has_image               text,
#                 latitude                float,
#                 longitude               float,
#                 bedrooms                float,
#                 square_feet             float,
#                 distance_from_city_center float,
#                 price_per_sqft          float,
#                 zip                     integer)""")
# sio = StringIO() # string buffer
# sio.write(data.to_csv(index=None, header=None))  # Write the Pandas DataFrame as a csv to the buffer
# sio.seek(0)  # reset the position

# # Copy the string buffer to the database
# with cursor as c:
#     c.copy_expert("""COPY listings FROM STDIN WITH (FORMAT CSV)""", sio)
#     connection.commit()

# Update the listings table
def update_listings_table(data, host_, port_, user_, password_, dbname_):

    # Connect
    try:
        connection = psycopg2.connect(
            host = host_,
            port = port_,
            user = user_,
            password = password_,
            dbname= dbname_
            )
        print('Connected to:', host_)
    except:
        print('Unable to conect to', host_)

    # Get initial row count
    old_row_count = pd.read_sql(""" SELECT count(*) FROM listings """,
                               connection)

    # Insert each row
    for row in range(len(data)):
        try:
            query = """ INSERT into listings (id, repost_of, name, url, datetime, last_updated, price, where_,
                                has_image, latitude, longitude, bedrooms, square_feet, distance_from_city_center,
                                price_per_sqft, zip)
                        SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        WHERE NOT EXISTS (SELECT id 
                                          FROM listings 
                                           WHERE id = %s)
                        """
            list_ = [data['id'].iloc[row],
                     data['repost_of'].iloc[row],
                     data['name'].iloc[row],
                     data['url'].iloc[row],
                     data['datetime'].iloc[row],
                     data['last_updated'].iloc[row],
                     data['price'].iloc[row],
                     data['where_'].iloc[row],
                     str(data['has_image'].iloc[row]),
                     data['latitude'].iloc[row],
                     data['longitude'].iloc[row],
                     data['bedrooms'].iloc[row],
                     data['square_feet'].iloc[row],
                     data['distance_from_city_center'].iloc[row],
                     data['price_per_sqft'].iloc[row],
                     data['zip'].iloc[row],               
                     data['id'].iloc[row]]                               
                        
            cursor = connection.cursor()
            cursor.execute(query, list_)
            connection.commit()            
        except:
            connection.rollback()
            print('Could not insert', data['id'].iloc[row])
    
    # Get new row counts
    new_row_count = pd.read_sql(""" SELECT count(*) FROM listings """,
                               connection)

    print('Rows updated:', 
           new_row_count['count'].iloc[0] - old_row_count['count'].iloc[0]
           )

# CLI function
def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--site", help= "craigslist site")
    parser.add_argument("-a","--area", help= "craigslist area")
    parser.add_argument("-sort","--sort_by", help= "craigslist sort param")
    parser.add_argument("-g","--geotagged", help= "craigslist geotagged param")
    parser.add_argument("-l","--limit", help= "limit of listings. Must be multiples of 120", type= int)
    parser.add_argument("-c","--category", help= "craigslist category")
    parser.add_argument("-rh", "--remote_host", help= "AWS RDS host")
    parser.add_argument("-p", "--port", help= "AWS RDS port")
    parser.add_argument("-u", "--user", help= "AWS RDS user")
    parser.add_argument("-pass", "--password", help= "AWS RDS password")
    parser.add_argument("-db", "--dbname", help= "AWS RDS db name")
    args = parser.parse_args()
    site = args.site
    area = args.area
    sort_by = args.sort_by
    geotagged = args.geotagged
    limit = args.limit
    category = args.category
    remote_host = args.remote_host
    port = args.port
    user = args.user
    password = args.password
    dbname = args.dbname

    # Get bedrooms and square feet
    print('Scraping extra features.......')
    extra_feats = extra_features(site, area, category, sort_by, limit)
    print('Complete.')

    # Get normal features
    print('Scraping normal features.......')
    main_feats = main_features(site, area, category, sort_by, limit, geotagged)
    print('Complete.')

    # Merge tables
    print('Formatting.......')
    all_features = pd.merge(main_feats, extra_feats, left_on='id', right_on='id')

    # Add Distance from city center
    all_features = calc_distance_from_city_center(all_features)

    # Add price per square feet
    all_features = price_per_sqft(all_features)
    print('Complete.')

    # Add zip codes
    print('Getting zip codes.......')
    geolocator = geopy.Nominatim(user_agent='zip_codes')

    all_features['zip'] = all_features.apply(get_zipcode, 
                                             axis=1, 
                                             geolocator=geolocator, 
                                             lat_field='latitude', 
                                             lon_field='longitude')
    print('Complete.')
    
    # Update postgres table
    update_listings_table(data = all_features, host_= remote_host, port_ = port, 
    user_ = user, password_ = password, dbname_ = dbname)

if __name__ == '__main__':
    main()
