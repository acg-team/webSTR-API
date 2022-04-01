#!/usr/bin/env python3
import argparse
from gtf_to_sql import connection_setup
import pandas as pd

from repeats.models import CRCVariation, Repeat

def make_db_variation(df_row, session):
    try:
        var_already_in_db = session.query(CRCVariation).filter_by(
            tcga_barcode = df_row["patient"],
            sample_type = df_row["sample_type"],
            start = df_row['start'],
            end = df_row['end']).one()
        return "Already exists in the database"
    except:
        # initialize instance of database CRCVariation
        db_variation = CRCVariation(
            tcga_barcode = df_row["patient"],
            sample_type = df_row["sample_type"],
            start = df_row['start'],
            end = df_row['end'],
            reference = df_row["ref"],
            alt = df_row["alt"],
            repeat_id = df_row["repeat_id"]
        )

        #try:
        repeat_id = df_row["repeat_id"]
        print(repeat_id)
        if repeat_id != '.':
            repeat = session.query(Repeat).get(int(repeat_id))
            repeat.crcvariations.append(db_variation)
        #except:
        #    print("This might be a PERF repeat, " + df_row["repeat_id"])
        return True

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path to where the repeat-containing database can be found"
    )
    parser.add_argument(
        "--var", "-v", type=str, required=True, help="Path to variations file in csv format"
    )
  
    return parser.parse_args()


def main():
    args = cla_parser()
    db_path = args.database
    input_path = args.var
    print("Connecting to the database")
    engine, session = connection_setup(db_path)

    df_var = pd.read_csv(input_path)

    df_var.apply(lambda row : make_db_variation(row, session), axis = 1)
  
    session.commit()

if __name__ == "__main__":
    main()
