#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np 
import json
from sqlalchemy import exc 
import sys 
import os

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
    output_path = "../data/repeats/EnsembleTR/repeats/sql_import/ensebmlTR_repeats_sql.csv"
    """
    if os.path.exists(output_path):
        repeats_df.to_csv(output_path, 
            columns = ["chr","start","end","motif","source","l_effective","region_length","n_effective","trpanel_id"],
            mode='a',
            index = False,
            header = False
        )
    else:
        repeats_df.to_csv(output_path, 
            columns = ["chr","start","end","motif","source","l_effective","region_length","n_effective","trpanel_id"],
            index = False,
            header = True
        )
    """
    return repeats_df

def main():
    args = cla_parser()
    db_path = args.db
    
    repeats_folder = '../data/repeats/EnsembleTR/repeats/'
    afreqs_folder = '../data/repeats/EnsembleTR/afreqs/'
    repeats_files = [f for f in os.listdir(repeats_folder) if os.path.isfile(os.path.join(repeats_folder, f))]
   
    for repeats_file in repeats_files:
        print(repeats_folder + repeats_file)
        repeats_df = pd.read_table(repeats_folder + repeats_file, converters={'Gene': json.loads})
        repeats_df = make_correct_csv_repeats(repeats_df)
   
        current_chr = repeats_df['chr'].iloc[0]

        afreqs_file = afreqs_folder + 'afreq_het_' + current_chr +'.csv'
        print(afreqs_file)
        
        afreqs_df = pd.read_table(afreqs_file, converters={'afreq_AFR': json.loads, 'afreq_AMR': json.loads, 'afreq_EAS': json.loads,
            'afreq_SAS': json.loads, 'afreq_EUR': json.loads })

        engine, session = connection_setup(db_path)

        for i, repeat in repeats_df.iterrows():
            print("Checking if repeat already exists")
            #print(Repeat.__table__.columns.keys())
            db_repeat = session.query(Repeat).filter ( 
                            Repeat.source == 'EnsembleTR',
                            Repeat.start == repeat.start,
                            Repeat.end == repeat.end,
                            Repeat.chr == repeat.chr
                        ).one_or_none()
            #print(db_repeat)
            if db_repeat is not None: 
                print("Found repeat in db")
                gene_ids = repeat["gene"]
                print(gene_ids)
                afreqs = afreqs_df[afreqs_df.ID == repeat.ID] 
                """
                db_afreqs = None
                #db_afreqs = session.query(AlleleFrequency).filter(AlleleFrequency.repeat_id ==  db_repeat.id).one_or_none()
        
                if db_afreqs is None:
                    print("Starting to populate afreqs")
                    # "1000 Genomes Africa" 
                    for l, freq in afreqs["afreq_AFR"].values[0].items():
                        db_afreqs = AlleleFrequency(
                            population = "1000 Genomes AFR",
                            n_effective = int(l),
                            frequency = freq,
                            het = afreqs["het_AFR"],
                            num_called = afreqs["numcalled_AFR"],
                            repeat_id = db_repeat.id
                        )
                        print(db_afreqs)
                        #db_repeat.allfreqs.append(db_afreqs)
                    for l, freq in afreqs["afreq_AMR"].values[0].items():
                        db_afreqs = AlleleFrequency(
                            population = "1000 Genomes AMR",
                            n_effective = int(l),
                            frequency = freq,
                            het = afreqs["het_AMR"],
                            num_called = afreqs["numcalled_AMR"],
                            repeat_id = db_repeat.id
                        )
                        #db_repeat.allfreqs.append(db_afreqs)
                    for l, freq in afreqs["afreq_EAS"].values[0].items():
                        db_afreqs = AlleleFrequency(
                            population = "1000 Genomes EAS",
                            n_effective = int(l),
                            frequency = freq,
                            het = afreqs["het_EAS"],
                            num_called = afreqs["numcalled_EAS"],
                            repeat_id = db_repeat.id
                        )
                        #db_repeat.allfreqs.append(db_afreqs)
                    for l, freq in afreqs["afreq_SAS"].values[0].items():
                        db_afreqs = AlleleFrequency(
                            population = "1000 Genomes SAS",
                            n_effective = int(l),
                            frequency = freq,
                            het = afreqs["het_SAS"],
                            num_called = afreqs["numcalled_SAS"],
                            repeat_id = db_repeat.id
                        )
                        #db_repeat.allfreqs.append(db_afreqs)
                    for l, freq in afreqs["afreq_EUR"].values[0].items():
                        db_afreqs = AlleleFrequency(
                            population = "1000 Genomes EUR",
                            n_effective = int(l),
                            frequency = freq,
                            het = afreqs["het_EUR"],
                            num_called = afreqs["numcalled_EUR"],
                            repeat_id = db_repeat.id
                        )
                        #db_repeat.allfreqs.append(db_afreqs)
                """    
                for gene_id in gene_ids:
                    if gene_id != "-":
                        try:
                            print(gene_id)
                            db_gene = session.query(Gene).filter(Gene.ensembl_version_id == gene_id).one()
                            # Add relationship to gene 
                            db_gene.repeats.append(db_repeat)
                            print(db_repeat.id, db_gene.id)
                        except exc.NoResultFound: 
                            print("couldnt find gene in our db")
            else: 
                print("Coulnd't find this repeat in db")
        
        session.commit()
 
if __name__ == "__main__":
    main()
