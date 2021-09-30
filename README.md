## How to start API locally on your machine

### Set environmental variable on your machine to 

`export DB_CONN="sqlite:///db/example.db"`

For linux, add this line to `~/.bashrc` and restart your terminal. 

### Start web server

Run the following command from the root folder of this repo: 

`uvicorn strAPI:main:app --reload`

### You can now access the api at `http://127.0.0.1:8000` 

## How to make it run via docker

Build an image from the strAPI directory

`docker build . -t strapi`

Run the current image in a container called `my_api`

`docker run --name my_api -d -p 8080:5000 strapi`

Now your API is available at `http://0.0.0.0:8080` and you can see the app logs with the following command: 

`docker logs my_api`