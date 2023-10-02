import os
import logging
import sys
from io import StringIO

from sqlmodel import create_engine, Session, SQLModel

from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory as AlembicScriptDirectory
from alembic.migration import MigrationContext

DATABASE_URL = os.environ['DATABASE_URL']

# Convert "postgres://<db_address>"  --> "postgresql+psycopg2://<db_address>" needed for SQLAlchemy
final_db_url = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://")  

""" 
WARNING: Alembic functionality was teste but not used by default. Treat it as a POC for future versions.

Check the database version and check if migrations need to be executed
There is support for executing migratiosn right away but calling alembic tool is more reliable
"""
def check_db_version(engine, config_file: str = os.path.join(os.path.split(__file__)[0], "../../alembic.ini")) -> None:
    
    alembic_cfg = AlembicConfig(config_file)
    script_location = os.path.join(os.path.split(config_file)[0],
                                   alembic_cfg.get_section(alembic_cfg.config_ini_section)["script_location"]
                                  )
    alembic_cfg.set_main_option('script_location', script_location)
    script_directory = AlembicScriptDirectory.from_config(alembic_cfg)

    with engine.begin() as connection:
      alembic_context = MigrationContext.configure(connection)
      current_db_version = alembic_context.get_current_revision()

    expected_db_version = script_directory.get_current_head()

    db_version_msg: str = f"Database: version check. current: {current_db_version}, expected: {expected_db_version}"
    logging.info(db_version_msg)

    if current_db_version == expected_db_version:
       logging.info(f"Database: version match {expected_db_version}. {final_db_url}")
    else:
        logging.info(f"Database: version mismatch")
        raise Exception(f"""
  {db_version_msg}
  You can use 'python -m alembic upgrade head' run migrations on the database.
  If that fails though you will need to use alembic tool and alembic.ini file to perform addtitional actions
  This can require changing database url in alembic.ini and running alembic upgrade head
  """) 

engine = create_engine(final_db_url, echo=False)

"""
WARNING: Alembic functionality was teste but not used by default. Treat it as a POC for future versions.
"""
if os.environ.get("WEBSTR_DATABASE_MIGRATIONS_ENABLE", "")  == "1":
  check_db_version(engine)

def get_db():
  with Session(engine) as session:
    yield session
