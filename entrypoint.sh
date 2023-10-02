#!/bin/bash

if [ ${WEBSTR_DATABASE_MIGRATE:-0} == "True" ]
then
    echo "Running database upgrade ${DATABASE_URL}"
    python -m alembic upgrade head
else
    echo "Skipping database upgrade"
fi

if [ ${WEBSTR_DATABASE_DATA_UPGRADE:-0} == "True" ]
then
    echo "Running database data insert ${DATABASE_URL}"
    cd database_setup
    bash full_db_setup.sh
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