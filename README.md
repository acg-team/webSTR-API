# About WebSTR-API

This repository is home to WebSTR-API - REST-full API for and backend for [WebSTR](http://webstr.ucsd.edu/) - portal of Human genome-wide variation in Short Tandem Repeats (STRs).
Our goal is to make large STR genotype datasets used by the broader genomics community by facilitating open access to this data. 

WebSTR is the result of collaboration between two scientific groups [Maria Anisimova’s Lab](https://github.com/acg-team) and [Melissa Gymrek’s Lab](https://github.com/gymrek-lab).

Source code for the WebSTR web portal can be found here: https://github.com/gymrek-lab/webstr

## How can I use the API? 

All the available endpoints are described in automatically generated documentation that includes Python code examples and can be accessed here - http://webstr-api.ucsd.edu/docs

## Can I set up the database and API locally on my machine?

Yes! It is possible and we encourage it if you would like to add your own data to WebSTR or perform any advanced analysis on it. 

## Can I deploy my own version of the WebSTR-API on University cluster?

Yes, for that please use provided Docker file, WebSTR-API can be deployed on any container-based service. 

### Instructions on how to set-up webSTR-API locally (for development): 

#### Step 0: Set up the database
 Install and configure PostgreSQL on your machine and create an empty database called strdb. We provide an sql_dump backup of the current version of the database on request. Restore the database from this backup. 
 
#### Step 1: Install all the requirements

a) Set up python3 and virtualenv on your machine:
[For Mac, follow instructions here.](https://gist.github.com/pandafulmanda/730a9355e088a9970b18275cb9eadef3)
You can also use conda, in this case follow this instructions to create conda env, it is preffered for newer [M1/2 Macs](https://towardsdatascience.com/how-to-manage-conda-environments-on-an-apple-silicon-m1-mac-1e29cb3bad12) and for infrustructures that already use conda. 
Activate your environment.
 
b) Create new virtual env and install all the requirements with the following command:

`pip install -r requirements.txt`

 
#### Step 2: Set environmental variable DATABASE_URL on your machine (or your IDE) to 

`export DATABASE_URL="postgres://postgres:YOURPASSWORD@localhost:5432/strdb"`

Note that this is using the default user postgres, if you created your db on a different user, adjust this variable accordingly. 

Optional: add this line to `~/.bashrc` and restart your terminal. 

#### Step 3: Start API server

Run the following command from the root folder of this repo: 

`uvicorn strAPI.main:app --host=0.0.0.0 --port=${PORT:-5000} --reload`

#### Step 4: You can now access the api at `http://0.0.0.0:5000` 
