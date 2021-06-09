#!/usr/bin/env python 3
""" Collection of convienence functions to use when working with a database ot the type constructed in this
project using setup_db.py and populate_db.py
"""
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from setup_db import Gene, Transcript, Exon

def get_sorted_exons(session, transcript, protein_coding=False):
    """ Retrieve all Exons associated with input Transcript and return in sorted order. Option to
    filter on protein coding Exons only

    Parameters
    session:    A session connected to the DB where the Exons and Transcripts live
    transcript (Transcript):
                Transcript for which the Exons will be retrieved
    protein_coding (Bool):
                If True, only protein coding Exons will be returned

    Returns
    List of (filtered) Exons, sorted by order of appearance in the protein, so for Transcripts from the 
    reverse strand, order will be descending.
    """
    exons = []
    for exon in transcript.exons:
        if protein_coding and not exon.cds:
            continue
        exons.append(exon)

    if transcript.gene.strand == "fw":
        return list(sorted(exons, key=lambda x : x.begin))
    elif transcript.gene.strand == "rv":
        return list(sorted(exons, key=lambda x : x.begin, reverse=True))


def main():
    db_handle = "/cfs/earth/scratch/verb/projects/CRC_STRs/results/test/db/test_brca2.db"
    engine = create_engine("sqlite:///{}".format(db_handle), echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    # emsembl_trans = "ENST00000380152.6"
    # emsembl_trans = "ENST00000623083.2"
    # transcript = session.query(Transcript).filter_by(ensembl_transcript=emsembl_trans).one()
    # for i in get_sorted_exons(session, transcript, protein_coding=True):
    #     print(i)

if __name__ == "__main__":
    main()
