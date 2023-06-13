#!/usr/bin/env python3
import sys
sys.path.append("..")

import argparse
import os
import io
import pandas as pd
import urllib.parse
import urllib.request
import gtfparse
from sqlalchemy import Index
from sqlalchemy import exc
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound
import mygene
from strAPI.repeats.models import Gene, Transcript, Exon, Genome

GENE_TYPE_NAME = "gene"
def get_genome_annotations(gtf_handle, protein_coding=True):
    """ Parsing and optional filtering of gtf genome annotation file into pd.DataFrame
    """
    gtf_df = gtfparse.read_gtf(gtf_handle)

    if protein_coding:
        # Select only protein coding genes from the gtf
        gtf_df = gtf_df.loc[(gtf_df["gene_type"] != "protein_coding")]

    return gtf_df

def add_genes(session, gtf_df, genome):
    """ Get desired field values for all genes from a gtf data frame. For each gene in the gtf file,
    create a Gene instance. Finally, add all encountered Genes to the session

    Parameters 
    session:        A SQLAlchemy session that is connected to a database where information from the genome
                    annotation file will be stored
    gtf_df (pd.DataFrame):  
                    Pandas data frame of gtf genome annotation file. Specifically one produced
                    using gtfparse.read_gtf()
    """
    gene_list = []
    gene_infos = query_gene_info(gtf_df)
    

    for index, row in gtf_df.loc[(gtf_df["feature"] == "gene")].iterrows():
        ensembl_id = row["gene_id"].split(".")[0]  # emsebl gene id without version number
        gene_info = gene_infos[ensembl_id]

        gene = Gene(
                ensembl_id = ensembl_id,
                ensembl_version_id = row["gene_id"],
                entrez_id = gene_info["entrezgene"],
                name = gene_info["symbol"],
                description = gene_info["name"],
                chr = row["seqname"],
                start = row["start"],
                end = row["end"],
                strand = row["strand"],
                genome_id = genome.id
            )
       
        gene_list.append(gene)
        genome.genes.append(gene)
    session.add_all(gene_list)

def query_gene_info(gtf_df, query_fields=["name", "symbol", "entrezgene"]):    
    ensembl_ids = set()
    for index, row in gtf_df.loc[(gtf_df["feature"] == "gene")].iterrows():
        ensembl_ids.add(row["gene_id"].split(".")[0])
    response = mygene.MyGeneInfo().getgenes(ensembl_ids, fields=",".join(query_fields))
    
    gene_infos = dict()
    not_found_counter = 0
    for result in response:
        try:
            # create placeholder dict if no info was found
            if result['notfound']:
                gene_infos[result['query']] = {                    
                    "symbol": None,
                    "name": None,
                    "entrezgene": None,
                }
                not_found_counter += 1
                continue
        except KeyError:
            # something was found, but need to check for each field whether it was found or not
            # otherwise they will be missing and KeyErrors will be raised later on
            for field in query_fields:
                    try:
                        result[field]
                    except KeyError:
                        result[field] = None
        gene_infos[result['query']] = result
    print(f"No gene information could be found for {not_found_counter} out of {len(ensembl_ids)} genes")
    return gene_infos

def add_transcripts(session, gtf_df):
    """ Get desired field values for all transcripts from a gtf data frame, add them to their respective
    genes in the session

    Parameters
    session:        A SQLAlchemy session that is connected to a database where information from the genome
                    annotation file will be stored
    gtf_df (pd.DataFrame):  
                    Pandas data frame of gtf genome annotation file. Specifically one produced
                    using gtfparse.read_gtf()
    """
    for index, row in gtf_df.loc[(gtf_df["feature"] == "transcript")].iterrows():     
        ensembl_id = row["gene_id"].split(".")[0]  # emsebl gene id without version number
        gene = session.query(Gene).filter_by(ensembl_id = ensembl_id).one()
        gene.transcripts.append(
            Transcript(
                ensembl_transcript=row["transcript_id"],
                start=row["start"],
                end=row["end"]
            )
        )

def add_exons(session, gtf_df):
    """ Get desired field values for all exons from a gtf data frame, add them to their transcripts
    in the session
    
    Parameters
    session:        A SQLAlchemy session that is connected to a database where information from the genome
                    annotation file will be stored
    gtf_df (pd.DataFrame):  
                    Pandas data frame of gtf genome annotation file. Specifically one produced
                    using gtfparse.read_gtf()
    """        
    # Multiple successive rows in the gtf file describe different features for one exon: exon, CDS, start_codon and stop_codon
    ## One exon can also appear multiple times in the same gtf file (for different transcripts)
    for index, row in gtf_df[gtf_df["feature"].isin({"exon", "CDS", "start_codon", "stop_codon"})].iterrows():
        if row["feature"] == "exon":   
            skip = False
            # get the transript the exon belongs to from the session
            transcript = session.query(Transcript).filter_by(ensembl_transcript = row["transcript_id"]).one()
            # get exon id from the row            
            ensembl_exon=row["exon_id"]            
            try:
                # if an Exon with this id was already generated for a prior Transcript, just add the Exon to
                ## the current Transcript. Also skip the next few rows that contain info on Exon features as 
                ### they should already be known from previous encounter
                existing_exon = session.query(Exon).filter_by(ensembl_exon=ensembl_exon).one()
                transcript.exons.append(existing_exon)
                skip = True
            except NoResultFound:
                # Exon was not observed before, make new Exon and parse feature information from the next few rows in the file
                new_exon = Exon(ensembl_exon=row["exon_id"], start=row["start"], end=row["end"], cds=False)            
                transcript.exons.append(new_exon)

        elif row["feature"] == "CDS" and not skip:
            # does the exon contain coding sequence?
            new_exon.cds = True

        elif row["feature"] == "start_codon" and not skip:
            # does the exon contain a start codon? If so: store the first position of the start codon
            new_exon.start_codon = row["start"]

        elif row["feature"] == "stop_codon" and not skip:
            # does the exon contain a stop codon? If so: store the first position of the stop codon
            new_exon.stop_codon = row["start"]

def connection_setup(db_path):
    # check if database exists
    #if not os.path.exists(db_path):
    #    raise FileNotFoundError("No DB was found at the specified handle")
    # connect to DB, initialize and configure session
    #engine = create_engine("sqlite:///{}".format(db_path), echo=False)   
    engine = create_engine(db_path, echo=False) 
    Session = sessionmaker(bind=engine)
    session = Session()

    return engine, session

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path where the (empty) database to be populated can be found. Empty DB can be generated using 'setup_db.py'"
    )
    parser.add_argument(
        "--gtf", "-g", type=str, required=True, help="Path where the gtf file with genome annotations can be found, this will be parsed and inserted into the DB"
    )

    # default for Sinergia GRCh38.p2 
    parser.add_argument(
        "--assembly", "-a", type=str, required=True, help="Genome assembly name in db"
    )

    return parser.parse_args()


def main():
    args = cla_parser()
    db_path = args.database
    gtf_handle = args.gtf
    assembly = args.assembly

    # db_path="sqlite:////Users/maxverbiest/PhD/projects/str_database/db/test.db"
    # gtf_handle="/Users/maxverbiest/PhD/projects/str_database/data/genome_anntotation/gencode_small_brca2_M.gtf"
    
    # check if gtf file exists
    if not os.path.exists(gtf_handle):
        raise FileNotFoundError("No gtf file was found at the specified handle")

    engine, session = connection_setup(db_path)

    # read in gtf file
    gtf_df = get_genome_annotations(gtf_handle, protein_coding=True)

    genome = session.query(Genome).filter(Genome.version == assembly).one()

    # add genes, transcripts and exons from the gtf file to the session
    add_genes(session, gtf_df, genome)
    add_transcripts(session, gtf_df)
    add_exons(session, gtf_df)

    # commit new additions to the database before adding indexes, otherwise sqlalchemy will complain
    ## that the 'database is locked'
    session.commit()

    # add indexes to row that will likely be queried a lot
    # ensembl ID columns for Gene, Transcript, Exon
    Index('ensembl_id_idx', Gene.ensembl_id).create(engine)
    Index('ensembl_transcript_idx', Transcript.ensembl_transcript).create(engine)
    Index('ensembl_exon_idx', Exon.ensembl_exon).create(engine)

    # commit
    session.commit()

if __name__ == "__main__":
    main()
