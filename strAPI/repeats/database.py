import os
from sqlmodel import create_engine, Session

DATABASE_URL = os.environ['DATABASE_URL']

# Convert "postgres://<db_address>"  --> "postgresql+psycopg2://<db_address>" needed for SQLAlchemy
final_db_url = "postgresql+psycopg2://" + DATABASE_URL.lstrip("postgres://")  

engine = create_engine(final_db_url, echo=False)

def get_db():
  with Session(engine) as session:
    yield session