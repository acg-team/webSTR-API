## How to start API locally on your machine

### Step 1: Install all the requirements

a) Set up python3 and virtualenv on your machine:
[For Mac, follow instructions here.](https://gist.github.com/pandafulmanda/730a9355e088a9970b18275cb9eadef3)

b) Create new virtual env and install all the requirements with the following command:
`pip3 install -r requirements.txt`

### Step 2: Set environmental variable on your machine to 

`export DATABASE_URL="postgresql+psycopg2://postgres:YOURPASSWORD@localhost:5432/strdb"`

For linux, add this line to `~/.bashrc` and restart your terminal. 

### Step 3: Start web server

Run the following command from the root folder of this repo: 

`uvicorn strAPI.main:app --host=0.0.0.0 --port=${PORT:-5000} --reload`

### Step 4: You can now access the api at `http://0.0.0.0:5000` 

## How to make it run via docker

Build an image from the strAPI directory

`docker build . -t strapi`

Run the current image in a container called `my_api`

`docker run --name my_api -d -p 8080:5000 strapi`

Now your API is available at `http://0.0.0.0:8080` and you can see the app logs with the following command: 

`docker logs my_api`
