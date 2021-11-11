import os
from sqlmodel import create_engine, Session
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
engine = psycopg2.connect(DATABASE_URL, sslmode='require')

def get_db():
  with Session(engine) as session:
    yield session