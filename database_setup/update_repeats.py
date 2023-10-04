#!/usr/bin/env python3
import argparse
from gtf_to_sql import connection_setup
import pandas as pd
import sys

sys.path.append("..")

from strAPI.repeats.models import Repeat, CRCVariation

def update_db_variation(df_row, session):
        try:
            repeat_id = df_row["repeat_id"]
           
            if repeat_id != '.':
                repeat = session.query(Repeat).get(int(repeat_id))
                db_variation = CRCVariation(
                    instable_calls = df_row["instable_calls"],
                    stable_calls = df_row["stable_calls"],
                    total_calls = df_row["total_calls"],
                    frac_variable = df_row["frac_variable"],
                    avg_size_diff = df_row["avg_size_diff"],
                    repeat_id = repeat_id
                )
                repeat.crcvariation = db_variation
        except:
            print("This might be a PERF repeat ")
            print(df_row)
        return True

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path to where the repeat-containing database can be found"
    )
    parser.add_argument(
        "--var", "-v", type=str, required=True, help="Path to repeats file in csv format"
    )
  
    return parser.parse_args()


def main():
    args = cla_parser()
    db_path = args.database
    db_path = db_path.replace("postgres://", "postgresql+psycopg2://") 
    
    input_path = args.var
    print("Connecting to the database")
    engine, session = connection_setup(db_path)

    df_var = pd.read_csv(input_path)

    df_var.apply(lambda row : update_db_variation(row, session), axis = 1)
  
    session.commit()

if __name__ == "__main__":
    main()
