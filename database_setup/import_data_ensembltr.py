#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np 
import json
from sqlalchemy import exc 
import sys 
sys.path.append("..")

from strAPI.repeats.models import Gene, Repeat, TRPanel, AlleleFrequency
from gtf_to_sql import connection_setup

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--db", "-d", type=str, required=True, help="Path to db"
    )
     
    return parser.parse_args()

def make_correct_csv_repeats(repeats_df):
    #    Chrom    Start      End Motif                     ID                   Gene      Source
    repeats_df.columns = ['chr', 'start', 'end', 'motif', 'ID', 'gene', 'source']
    
    # Calculate l_effective = length(motif)
    repeats_df['l_effective'] = repeats_df['motif'].str.len()
    
    # Calculate region length
    repeats_df['region_length'] = (repeats_df['end'] - repeats_df['start']) + 1
    
    # Calculate n_effective
    repeats_df['n_effective'] = (repeats_df['region_length'] / repeats_df['l_effective']).astype(int)

    # Fill in trpanel_id
    repeats_df['trpanel_id'] = [3] * len(repeats_df)
    
    # Output file needed for sql import of repeats
    repeats_df.to_csv("../data/repeats/ensebmlTR_processed.csv", 
        columns = ["chr","start","end","motif","source","l_effective","region_length","n_effective","trpanel_id"],
        index = False
    )
    return repeats_df

def main():
    args = cla_parser()
    db_path = args.db
    
    repeats_file = '../data/repeats/repeat_info_chr21.tsv'
    repeats_df = pd.read_table(repeats_file, converters={'Gene': json.loads})
    repeats_df = make_correct_csv_repeats(repeats_df)

    afreqs_file = '../data/repeats/afreq_het_chr21.tsv'
    
    afreqs_df = pd.read_table(afreqs_file, converters={'afreq_AFR': json.loads, 'afreq_AMR': json.loads, 'afreq_EAS': json.loads,
        'afreq_SAS': json.loads, 'afreq_EUR': json.loads })

    engine, session = connection_setup(db_path)

    for i, repeat in repeats_df.iterrows():
        db_repeat = session.query(Repeat).filter ( 
                        Repeat.source == 'EnsembleTR',
                        Repeat.start == repeat.start,
                        Repeat.end == repeat.end,
                        Repeat.chr == repeat.chr
                    ).one_or_none()
        if db_repeat is not None: 
            gene_ids = repeat["gene"]

            afreqs = afreqs_df[afreqs_df.ID == repeat.ID] 

            db_afreqs = session.query(AlleleFrequency).filter(AlleleFrequency.repeat_id ==  db_repeat.id).one_or_none()
    
            if db_afreqs is None:
                db_afreqs = AlleleFrequency(
                    afreq_AFR = afreqs["afreq_AFR"].values[0],
                    het_AFR = afreqs["het_AFR"],
                    numcalled_AFR =  afreqs["numcalled_AFR"],
                    afreq_AMR = afreqs["afreq_AMR"].values[0],
                    het_AMR = afreqs["het_AMR"],
                    numcalled_AMR = afreqs["numcalled_AMR"],
                    afreq_EAS =  afreqs["afreq_EAS"].values[0],
                    het_EAS = afreqs["het_EAS"],
                    numcalled_EAS = afreqs["numcalled_EAS"],
                    afreq_SAS = afreqs["afreq_SAS"].values[0],
                    het_SAS = afreqs["het_SAS"],
                    numcalled_SAS = afreqs["numcalled_SAS"],
                    afreq_EUR = afreqs["afreq_EUR"].values[0],
                    het_EUR = afreqs["het_EUR"],
                    numcalled_EUR = afreqs["numcalled_EUR"],
                    repeat_id = db_repeat.id
                )

                db_repeat.allfreq = db_afreqs
                
            for gene_id in gene_ids:
                if gene_id != "-":
                    try:
                        print(gene_id)
                        db_gene = session.query(Gene).filter(Gene.ensembl_version_id == gene_id).one()
                        # Add relationship to gene 
                        #db_gene.repeats.append(db_repeat)
                        print(db_repeat.id, db_gene.id)
                    except exc.NoResultFound: 
                        print("couldnt find gene in our db")
        else: 
            print("Coulnd't find this repeat in db")
    
    session.commit()

if __name__ == "__main__":
    main()
