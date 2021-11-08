import os

#from sqlalchemy import create_engine
#from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy.orm import sessionmaker

from sqlmodel import create_engine, Session

SQLALCHEMY_DATABASE_URL = os.getenv("DB_CONN")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
  with Session(engine) as session:
    yield session