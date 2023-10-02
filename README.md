# About WebSTR-API

This repository is home to WebSTR-API - REST-full API for and backend for [WebSTR](http://webstr.ucsd.edu/) - portal of Human genome-wide variation in Short Tandem Repeats (STRs).
Our goal is to make large STR genotype datasets used by the broader genomics community by facilitating open access to this data. 

WebSTR is the result of collaboration between two scientific groups [Maria Anisimova’s Lab](https://github.com/acg-team) and [Melissa Gymrek’s Lab](https://github.com/gymrek-lab).

Source code for the WebSTR web portal can be found here: https://github.com/gymrek-lab/webstr

## How to use the API? 

All the available endpoints are described in automatically generated documentation that includes Python code examples and can be accessed here - http://webstr-api.ucsd.edu/docs

For some example queries to get you started, check out [our Getting Started Guide](https://github.com/acg-team/webSTR-API/blob/main/GETTING_STARTED.md)

## Can I deploy my own version of the WebSTR-API on University cluster?

Yes, for that please use provided Docker file, WebSTR-API can be deployed on any container-based service.  

## Can I set up the database and API locally on my machine?

Yes! It is possible and we encourage it if you would like to add your own data to WebSTR or perform any advanced analysis on it. 

### Instructions on how to set-up webSTR-API locally (for development): 

#### Step 0: (docker and local ways) Set up the database 
 Install and configure PostgreSQL on your machine and create an empty database called strdb. We provide an sql_dump backup of the current version of the database on request. Restore the database from this backup. 

 Alternatively you can use `docker compose` with provided docker-compose.yml file to set up the PostgreSQL database.
 1. rename `.env.example` to `.env`
 2. copy backup to folder ./db/docker_data/pgdata/webstr_backup.dump
 2. `docker compose up -d db`
 3. `docker exec -it webstr-api-db-1 pg_restore -d strdb /var/lib/postgresql/data/pgdata/webstr_backup.dump`

#### Step 1: (only for non-docker way) Install all the requirements 


a) Set up python3 and virtualenv on your machine:
[For Mac, follow instructions here.](https://gist.github.com/pandafulmanda/730a9355e088a9970b18275cb9eadef3)
You can also use conda, in this case follow this instructions to create conda env, it is preffered for newer [M1/2 Macs](https://towardsdatascience.com/how-to-manage-conda-environments-on-an-apple-silicon-m1-mac-1e29cb3bad12) and for infrustructures that already use conda. 
Activate your environment.
 
b) Create new virtual env and install all the requirements with the following command:

`pip install -r requirements.txt`

 
#### Step 2: (only for non-docker way) Set environmental variable DATABASE_URL on your machine (or your IDE) to 
`export DATABASE_URL="postgres://postgres:YOURPASSWORD@localhost:5432/strdb"`

Note that this is using the default user postgres, if you created your db on a different user, adjust this variable accordingly. 

Optional: add this line to `~/.bashrc` and restart your terminal. 

#### Step 3: (only for non-docker way) Start API server  

Run the following command from the root folder of this repo: 

`uvicorn strAPI.main:app --host=0.0.0.0 --port=${PORT:-5000} --reload`

#### Step 4: You can now access the api at `http://localhost:5000` 

***

### How to build and run application using docker way

#### Step 0: Set up the database 
##### if you want to use PostgreSQL and backup
See docker part of Step 1 from the previous instructions
##### if sqlite is enough
Change database url in .env file to DATABASE_URL=sqlite:///db/debug.sqlite
Set WEBSTR_DATABASE_DATA_UPGRADE=True and WEBSTR_DEVELOPMENT=True in .env file
#### Step 1: Start containers
Run `docker compose up`

Now you can access api on localhost:5000 and frontend on localhost:5001

##### debugging in docker container
If you want to debug the code and you use VSCode - you can run code in container using vscode and tasks defined in launch.json in .vscode folder. Or you can use devcontaienr plugin to do the same. This is a bit more advanced, so you need to study how debuggin in containers works in vscode a bit before that. And you will have to stop webster-api-api-1 container first if you have it running through docker compose.

***

## How to build the database from scratch or import my own data to WebSTR? 

We recommend to start from making it work locally on your machine from a ready sql_dump that we provide upon request. Se instructions above. 
We also provide Python scripts for working with the ORM (abstraction layer on top of the database) to import new data into database. 
Explore "database_setup" directory for different utilities to import data into the database. 

* If you would like to **add a new genome assembly** see utility add_genomes. Example usage:

  `python add_genomes.py -d PATH_TO_DB`  

  Modify the script according to your data. 

  You will also need to import a GTF file corresponding to this assembly using gtf_to_sql.py 

  Genes, transcripts and exoms currently available for hg38(GRCh38.p2) assembly have been imported from [Encode](https://www.encodeproject.org/files/gencode.v22.annotation/).

* To **add a new reference panel** description and **study cohort**, use add_panels_and_cohorts.py

* If you would like **to import a new reference panel** we recommend making a csv corresponding to the repeats table structure and importing it directly to SQL to save time. Alternatively see  ` insert_repeats.py ` and 
` import_data_ensembltrs.py `  utilities that we made for repeats data coming  in different formats. Feel free to contact us for more details if you would like to make your own reference STR panel. 

***

### Database migrations using Alembic - Proof of Concept, not used in production.
@slmjy added alembic migrations as a proof of concept to the codebase.
Following changes were introduced:
1. Database migrations in /database_setup/migrations
2. alembic.ini and env.py files 
3. entrypoint.sh can run alembic migratiosn given environment variable WEBSTR_DATABASE_MIGRATE is set to True
4. in database.py there is a disabled check if database is on the latest version

If someone wants to start using alembic migrations, they can enable the version check and start generating new migrations using alembic and using them in production.