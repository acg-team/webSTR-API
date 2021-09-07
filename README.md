# How to start API locally? 

## Set environmental variable on your machine to 

`export DB_CONN="sqlite:///db/example.db"`

For linux, add this line to `~/.bashrc` and restart your terminal. 

## Start web server

Go to strAPI directory and run the following command: 

`uvicorn main:app --reload`

## You can now access the api at `http://127.0.0.1:8000` 