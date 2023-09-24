"""
This script imports gene expression and repeat length correlation data from a csv file into a database. 
It uses the gtf_to_sql module to connect to the database and the pandas module to read the csv file.
It inserts data into CRCExprRepeatLenCorr model.

The script defines a command-line interface using the argparse module.
The script can be run from the command line with the --database and --file arguments to specify the database and csv file paths.

Script can be run multiple times. It will update existing records and insert new ones.
"""

#!/usr/bin/env python3
import argparse
import logging
from gtf_to_sql import connection_setup
import pandas as pd

from strAPI.repeats.models import Gene, Repeat, CRCExprRepeatLenCorr


def update_db_record(df_row, session, genes_by_code, inserted_entities):

    def get_repeat(tmp_id, range=False):
        chr, start = tmp_id.split("_")
        start = int(start)
        query = session.query(Repeat).filter_by(chr=chr.lower())
        if range:
            query = query.filter(Repeat.start<=start).filter(Repeat.end>start)
        else:
            query = query.filter_by(start=start)
        return query.first()

    repeat = get_repeat(df_row["tmp_id"].strip())
    gene = genes_by_code.get(df_row["gene"].strip())

    repeat_id = None
    gene_id = None

    if repeat is None:
        logging.info(
            f"Repeat {len(inserted_entities)} with code {df_row['tmp_id']} not found in database. Trying range search.")
        repeat = get_repeat(df_row["tmp_id"].strip(), range=True)
        if repeat is None:
            logging.info(
                    f"Repeat {len(inserted_entities)} with code {df_row['tmp_id']} not found in database.")
        
    if gene is None:
        logging.info(
            f"Gene {len(inserted_entities)} with code {df_row['gene']} not found in database.")

    if repeat is not None and gene is not None:
        gene_id = gene.id
        repeat_id = repeat.id
    else:
        return

    entity = session.query(CRCExprRepeatLenCorr).filter_by(
        repeat_id=repeat_id,
        gene_id=gene_id
    ).first()

    if entity is None:

        entity = CRCExprRepeatLenCorr(
            repeat_id   = repeat_id,
            gene_id     = gene_id
        )

        session.add(entity)
    
    entity.gene_id = gene_id
    entity.repeat_id = repeat_id
    entity.coefficient = df_row["coefficient"]
    entity.intercept = df_row["intercept"]
    entity.p_value = df_row["pvalue_coef"]
    entity.p_value_corrected = df_row["pvalue_corrected"]

    inserted_entities.append(entity)


def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path to where the repeat-containing database can be found"
    )
    parser.add_argument(
        "--file", "-f", type=str, required=True, help="Path to variations file in csv format"
    )

    return parser.parse_args()


def main():
    args = cla_parser()
    db_path = args.database
    input_path = args.file
    logging.info("Connecting to the database")
    engine, session = connection_setup(db_path)

    inserted_entities = []

    logging.info("Getting all genes from database")
    genes_by_ensemble_code = {}
    for gene in session.query(Gene).all():
        genes_by_ensemble_code[gene.ensembl_id] = gene
    logging.info(f"Got {len(genes_by_ensemble_code)} genes from database")

    logging.info("Inserting gene expretion and repeat length correlation")
    data_frame = pd.read_csv(input_path)
    input_csv_len = len(data_frame)
    data_frame.apply(lambda row: update_db_record(row, session,
                     genes_by_ensemble_code, inserted_entities), axis=1)
    logging.info(
        f"""
            Inserted or updated {len(inserted_entities)} entities out of {input_csv_len}
        """)

    session.commit()

    logging.info("Inserting gene expretion and repeat length correlation")


if __name__ == "__main__":
    main()
