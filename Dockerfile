FROM python:3.8-slim-buster as base
LABEL maintainer="merenlin -- follow me on medium https://medium.com/@merenlin"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN mkdir -p /usr/src/strs
WORKDIR /usr/src/strs

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y gcc python3-dev build-essential  && \
    python -m pip install -r requirements.txt --no-cache-dir  && \
    apt-get remove -y gcc python3-dev build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV DATABASE_URL=sqlite:///db/debug.db

FROM base as prod
LABEL maintainer="merenlin -- follow me on medium https://medium.com/@merenlin"

RUN adduser -u 1000 --disabled-password --gecos "" appuser && chown -R appuser /usr/src/strs
USER appuser

COPY . .

ARG PORT=5000
EXPOSE $PORT

ENTRYPOINT [ "bash", "entrypoint.sh"]


