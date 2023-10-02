#!/bin/bash

echo "Running webstrcontainer with parameters: DATABASE_URL='${DATABASE_URL:-0}' WEBSTR_DATABASE_DATA_UPGRADE='${WEBSTR_DATABASE_DATA_UPGRADE:-0}'"

if [ ${WEBSTR_DATABASE_MIGRATE:-0} == "True" ]
then
    echo "Running alembic database migrations ${DATABASE_URL}"
    python -m alembic upgrade head
else
    echo "Skipping alembic database migrations"
fi

if [ ${WEBSTR_DATABASE_DATA_UPGRADE:-0} == "True" ]
then
    echo "Running database creation script"
    cd database_setup
    echo "Running database schema"
    python setup_db.py --database "${DATABASE_URL}"
    
    echo "Running database data insert asyncronously"
    bash full_db_setup.sh &
    cd ..
else
    echo "Skipping database  data insert"
fi

if [ ${WEBSTR_DEVELOPMENT:-0} == "True" ]
then
    uvicorn strAPI.main:app --host=0.0.0.0 --port=${PORT:-5000} --log-level debug --reload --reload-include strAPI
else
    uvicorn strAPI.main:app --host=0.0.0.0 --port=${PORT:-5000}
fi