# final_project_436
The code for the final project of msds436

### etl.py
This will scrape Craigslist and store the output in an RDS PostgrsSQL database. A table called listings will already need to be created with the below schema:

id                      bigint
repost_of               bigint
name                    text
url                     text
datetime                timestamp
last_updated            timestamp
price                   float
where_                  text
has_image               text
latitude                float
longitude               float
bedrooms                float
square_feet             float
distance_from_city_center float
price_per_sqft          float
zip                     integer

Command line arguments:
"-s","--site", help= "craigslist site"
"-a","--area", help= "craigslist area"
"-sort","--sort_by", help= "craigslist sort param"
"-g","--geotagged", help= "craigslist geotagged param"
"-l","--limit", help= "limit of listings. Must be multiples of 120", type= int
"-c","--category", help= "craigslist category"
"-rh", "--remote_host", help= "AWS RDS host"
"-p", "--port", help= "AWS RDS port"
"-u", "--user", help= "AWS RDS user"
"-pass", "--password", help= "AWS RDS password"
"-db", "--dbname", help= "AWS RDS db name"

CL example:
-s chicago -a chc -sort newest -g True -l 3000  -c apa -rh [remote hose] -p 5432 -u [user] -pass [password]  -db [datbase name]

### eda.ipynb
This is a jupyter notebook thatexplores the data set

### model.py
This script created a model using the cragslist data and scikit learn's GradientBoostingRegressor. The model will be saved in your working directory for future use.

Command line arguments:
"-rh", "--remote_host", help= "AWS RDS host"
"-p", "--port", help= "AWS RDS port"
"-u", "--user", help= "AWS RDS user"
"-pass", "--password", help= "AWS RDS password"
"-db", "--dbname", help= "AWS RDS db name"

CL example:
-rh [remote hose] -p 5432 -u [user] -pass [password]  -db [datbase name]

### predict.py
This script will take user input for a new listing and give a recommendation on what the monthly rent should be.

Command line arguments. Please note has_pics needs to be either True or False:
"-mf", "--modelfile_name", help= "SAV file that has the model"
"-c", "--cols", help= "The columns file "
"-sf", "--square_ft", help= "Square ft of unit to list"
"-d", "--dist_from_dt", help= "unit's distance from city center"
"-b", "--beds", help= "unit's number of bedrooms"
"-p", "--has_pics", help= "Does the unit have pictures?"
"-z", "--zip", help= "unit's zip code"

CL example:
-mf model.sav -c columns.csv -sf 1200 -d .75 -b 2 -p True -z 60622
