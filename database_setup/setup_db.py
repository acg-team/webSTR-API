#!/usr/bin/env python3
import sys
sys.path.append("..")

import argparse
import os


from strAPI.repeats.models import *
from sqlmodel import create_engine, SQLModel

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Handle where the (empty) database will be generated. Database can be populated using 'gtf_to_sqlite.py'"
    )

    return parser.parse_args()

def main():
    # db_handle = "sqlite:////Users/maxverbiest/PhD/projects/str_database/db/test.db"

    args = cla_parser()
    db_handle = args.database

    #if os.path.exists(db_handle):
    #    raise FileExistsError("A database already exists at specified handle, exiting!")

    engine = create_engine(db_handle, echo=True)
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    main()
