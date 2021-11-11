#!/usr/bin/env python3
import argparse
import os


from repeats.models import  Gene, Exon, Transcript, Repeat, CRCVariation, RepeatTranscriptsLink, ExonTranscriptsLink
from sqlmodel import create_engine, SQLModel

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Handle where the (empty) database will be generated. Database can be populated using 'gtf_to_sqlite.py'"
    )

    return parser.parse_args()

def main():
    # db_handle = "/cfs/earth/scratch/verb/projects/CRC_STRs/results/test/db/test.db"

    args = cla_parser()
    db_handle = args.database

    #if os.path.exists(db_handle):
    #    raise FileExistsError("A database already exists at specified handle, exiting!")

    engine = create_engine(db_handle, echo=True)
    SQLModel.metadata.create_all(engine)

if __name__ == "__main__":
    main()
