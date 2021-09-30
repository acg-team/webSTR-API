#!/usr/bin/env python3
import argparse
import os

import gtfparse
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, CheckConstraint, UniqueConstraint, Table
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Gene(Base):
    __tablename__ = "genes"

    id = Column(Integer, primary_key=True)
    ensembl_gene = Column(String, nullable=False, unique=True)
    chromosome = Column(String, nullable=False)
    strand = Column(String, CheckConstraint("strand in ('fw', 'rv')"), nullable=False)
    begin = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)    

    def __repr__(self):
        return "Gene(ensembl_gene={}, chromosome={}, strand={}, begin={}, end={})".format(
            self.ensembl_gene,
            self.chromosome,
            self.strand,
            self.begin,
            self.end
        )


# Association table for the many to many relationship between exons and transcripts
exons_transcripts = Table("exons_transcripts", Base.metadata,
    Column("exon_id", ForeignKey("exons.id"), primary_key=True),
    Column("transcript_id", ForeignKey("transcripts.id"), primary_key=True)
)

# Association table for the many to many relationship between repeats and transcripts
repeats_transcripts = Table("repeats_transcripts", Base.metadata,
    Column("repeat_id", ForeignKey("repeats.id"), primary_key=True),
    Column("transcript_id", ForeignKey("transcripts.id"), primary_key=True)
)

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True)
    ensembl_transcript = Column(String, nullable=False, unique=True)
    begin = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)

    # one to many Gene -> Transcripts
    gene_id = Column(Integer, ForeignKey("genes.id"))
    gene = relationship("Gene", back_populates="transcripts")

    # many to many Exons <-> Transcripts
    exons = relationship('Exon',
                            secondary=exons_transcripts,
                            back_populates='transcripts')

    # # many to many Repeats <-> Transcripts
    repeats = relationship('Repeat',
                            secondary=repeats_transcripts,
                            back_populates='transcripts')

    def __repr__(self):
        return "Transcript(ensembl_transcript={}, begin={}, end={})".format(
            self.ensembl_transcript,
            self.begin,
            self.end
        )

# Add relationship directive to Gene class for one to many Gene -> Transcript
Gene.transcripts = relationship("Transcript", order_by=Transcript.id, back_populates="gene")


class Exon(Base):
    __tablename__ = "exons"

    id = Column(Integer, primary_key=True)
    ensembl_exon = Column(String, nullable=False, unique=True)
    begin = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    cds = Column(Boolean, nullable=False)
    start_codon = Column(Integer)
    stop_codon = Column(Integer)

    # many to many Exons <-> Transcripts
    transcripts = relationship('Transcript',
                            secondary=exons_transcripts,
                            back_populates='exons')

    def __repr__(self):
        return "Exon(ensembl_exon={}, begin={}, end={}, cds={}, start_codon={}, stop_codon={})".format(
            self.ensembl_exon,
            self.begin,
            self.end,
            self.cds,
            self.start_codon,
            self.stop_codon
        )


class Repeat(Base):
    __tablename__ = "repeats"

    id = Column(Integer, primary_key=True)   
    source = Column(String, nullable=True, default="unknown")  # e.g. which detector found this Repeat?
    msa = Column(String, nullable=True)
    begin = Column(Integer, nullable=False)
    end = Column(Integer, nullable=False)
    l_effective = Column(Integer, nullable=False)
    n_effective = Column(Integer, nullable=False)
    region_length = Column(Integer, nullable=False)
    score_type = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    p_value = Column(Float, nullable=False)
    divergence = Column(Float, nullable=False)

    # one to many Gene -> Repeats
    gene_id = Column(Integer, ForeignKey("genes.id"))
    gene = relationship("Gene", back_populates="repeats")

    # many to many Repeats <-> Transcripts
    transcripts = relationship('Transcript',
                            secondary=repeats_transcripts,
                            back_populates='repeats')

    def __repr__(self):
        return "Repeat(source={}, msa={}, begin={}, end={}, l_effective={}, n_effective={}, region_length={}, score_type={}, score={}, p_value={}, divergence={})".format(
            self.source,
            self.msa,
            self.begin,
            self.end,
            self.l_effective,
            self.n_effective,
            self.region_length,
            self.score_type,
            self.score,
            self.p_value,
            self.divergence
        )

# Add relationship directive to Gene class for one to many Gene -> Repeats
Gene.repeats = relationship("Repeat", order_by=Repeat.id, back_populates="gene")


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

    if os.path.exists(db_handle):
        raise FileExistsError("A database already exists at specified handle, exiting!")

    engine = create_engine("sqlite:///{}".format(db_handle), echo=False)
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    main()
