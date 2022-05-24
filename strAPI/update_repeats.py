#!/usr/bin/env python3
import argparse
from gtf_to_sql import connection_setup
import pandas as pd

from repeats.models import Repeat

def update_db_variation(df_row, session):
        try:
            repeat_id = df_row["repeat_id"]
            print(repeat_id)
            if repeat_id != '.':
                repeat = session.query(Repeat).get(int(repeat_id))
                repeat.instable_calls = df_row["instable_calls"]
                repeat.stable_calls = df_row["stable_calls"]
                repeat.total_calls = df_row["total_calls"]
                repeat.frac_variable = df_row["frac_variable"]
                repeat.avg_size_diff = df_row["avg_size_diff"]
        except:
            print("This might be a PERF repeat, " + df_row["repeat_id"])
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
    input_path = args.var
    print("Connecting to the database")
    engine, session = connection_setup(db_path)

    df_var = pd.read_csv(input_path)

    df_var.apply(lambda row : update_db_variation(row, session), axis = 1)
  
    session.commit()

if __name__ == "__main__":
    main()
