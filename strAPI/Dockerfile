FROM python:3.8-slim-buster
LABEL maintainer="merenlin -- follow me on medium https://medium.com/@merenlin"

RUN apt-get update && apt-get install -y python3-dev build-essential

RUN mkdir -p /usr/src/strAPI
WORKDIR /usr/src/strAPI

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENV DB_CONN="sqlite:///db/example.db"

EXPOSE 5000

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "main:app"]
