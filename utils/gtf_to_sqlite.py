#!/usr/bin/env python3
import argparse
import os

import gtfparse
from sqlalchemy import Index
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import NoResultFound

from setup_db import Gene, Transcript, Exon


def get_genome_annotations(gtf_handle, protein_coding=True):
    """ Parsing and optional filtering of gtf genome annotation file into pd.DataFrame
    """
    gtf_df = gtfparse.read_gtf(gtf_handle)

    if protein_coding:
        # Select only protein coding genes from the gtf
        gtf_df = gtf_df.loc[(gtf_df["gene_type"] == "protein_coding")]

    return gtf_df

def add_genes(session, gtf_df):
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
    for index, row in gtf_df.loc[(gtf_df["feature"] == "gene")].iterrows():
        gene = Gene(
                ensembl_gene = row["gene_id"],
                chromosome = row["seqname"],
                begin = row["start"],
                end = row["end"]
            )
        # Strands are listed as '+' and '-' in gtf files
        if row["strand"] == "+":
            gene.strand = "fw"
        elif row["strand"] == "-":
            gene.strand = "rv"
        else:
            raise ValueError("Unknown strand identifier encountered, gtf indexes may be off")
        gene_list.append(gene)

    session.add_all(gene_list)

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
        ensembl_gene = row["gene_id"]
        gene = session.query(Gene).filter_by(ensembl_gene = ensembl_gene).one()
        gene.transcripts.append(
            Transcript(
                ensembl_transcript=row["transcript_id"],
                begin=row["start"],
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
                new_exon = Exon(ensembl_exon=row["exon_id"], begin=row["start"], end=row["end"], cds=False)            
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
    if not os.path.exists(db_path):
        raise FileNotFoundError("No DB was found at the specified handle")
    # connect to DB, initialize and configure session
    engine = create_engine("sqlite:///{}".format(db_path), echo=False)   
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

    return parser.parse_args()


def main():
    args = cla_parser()
    db_path = args.database
    gtf_handle = args.gtf
    
    # check if gtf file exists
    if not os.path.exists(gtf_handle):
        raise FileNotFoundError("No gtf file was found at the specified handle")

    engine, session = connection_setup(db_path)

    # read in gtf file
    gtf_df = get_genome_annotations(gtf_handle, protein_coding=True)

    # add genes, transcripts and exons from the gtf file to the session
    add_genes(session, gtf_df)
    add_transcripts(session, gtf_df)
    add_exons(session, gtf_df)

    # commit new additions to the database before adding indexes, otherwise sqlalchemy will complain
    ## that the 'database is locked'
    session.commit()

    # add indexes to row that will likely be queried a lot
    # ensembl ID columns for Gene, Transcript, Exon
    Index('ensembl_gene_idx', Gene.ensembl_gene).create(engine)
    Index('ensembl_transcript_idx', Transcript.ensembl_transcript).create(engine)
    Index('ensembl_exon_idx', Exon.ensembl_exon).create(engine)

    # commit
    session.commit()

if __name__ == "__main__":
    main()
