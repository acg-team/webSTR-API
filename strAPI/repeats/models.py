from typing import Optional, List
from sqlalchemy import Integer, String, Float, ForeignKey, Boolean, CheckConstraint, UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship

class ExonTranscriptsLink(SQLModel, table=True):
    __tablename__ = "exons_transcripts"
    exon_id: Optional[int] = Field(
        default=None, foreign_key="exons.id", primary_key=True
    )
    transcript_id: Optional[int] = Field(
        default=None, foreign_key="transcripts.id", primary_key=True
    )

class RepeatTranscriptsLink(SQLModel, table=True):
    __tablename__ = "repeats_transcripts"
    repeat_id: Optional[int] = Field(
        default=None, foreign_key="repeats.id", primary_key=True
    )
    transcript_id: Optional[int] = Field(
        default=None, foreign_key="transcripts.id", primary_key=True
    )

class GenesRepeatsLink(SQLModel, table=True):
    __tablename__ = "genes_repeats"
    repeat_id: Optional[int] = Field(
        default=None, foreign_key="repeats.id", primary_key=True
    )
    gene_id: Optional[int] = Field(
        default=None, foreign_key="genes.id", primary_key=True
    )

class CRCVariation(SQLModel, table=True):
    __tablename__ = "crcvariations"

    id: int = Field(primary_key=True)   
    tcga_barcode: str = Field(nullable=False)
    sample_type: str = Field(nullable=False)
    reference: int = Field(nullable=False)
    alt: int = Field(nullable=False)

    # one to many Repeat -> CRCVariation
    repeat_id: int = Field(foreign_key ="repeats.id")
    repeat: "Repeat" = Relationship(back_populates="crcvariations")

    def __repr__(self):
        return "CRCVariation(tcga_barcode={}, reference_period={}, period={})".format(
            self.tcga_barcode,
            self.reference_period,
            self.period,
        )

class Repeat(SQLModel, table=True):
    __tablename__ = "repeats"

    id: int = Field(primary_key=True)   
    source: Optional[str] = Field(default="unknown")# e.g. which detector found this Repeat?
    msa: str = Field(nullable=True)
    start: int = Field(nullable=False)
    end: int = Field(nullable=False)
    l_effective: int = Field(nullable=False)
    n_effective: int = Field(nullable=False)
    region_length: int = Field(nullable=False)
    score_type: str = Field(nullable=False)
    score: float = Field(nullable=False)
    p_value: float = Field(nullable=False)
    divergence: float = Field(nullable=False)

    # one to many Gene -> Repeats
    # gene_id: int = Field(foreign_key = "genes.id")
    # gene: "Gene" = Relationship(back_populates="repeats")
    # Add relationship directive to Repeat class for one to many Repeat -> CRCVariation
    crcvariations : List[CRCVariation] = Relationship(back_populates="repeat")
    # many to many Repeats <-> Transcripts
    transcripts: List["Transcript"] = Relationship(back_populates="repeats", link_model = RepeatTranscriptsLink)
    # many to many Gene <-> Repeat
    genes: List["Gene"] = Relationship(back_populates="repeats", link_model = GenesRepeatsLink)

    def __repr__(self):
        return "Repeat(source={}, msa={}, start={}, end={}, l_effective={}, n_effective={}, region_length={}, score_type={}, score={}, p_value={}, divergence={})".format(
            self.source,
            self.msa,
            self.start,
            self.end,
            self.l_effective,
            self.n_effective,
            self.region_length,
            self.score_type,
            self.score,
            self.p_value,
            self.divergence
        )

class Transcript(SQLModel, table=True):
    __tablename__ = "transcripts"
    __table_args__ = (UniqueConstraint("ensembl_transcript"),)
    id: int = Field(primary_key=True)
    ensembl_transcript: str = Field(nullable=False)
    start: int = Field(nullable=False)
    end: int = Field(nullable=False)

    # one to many Gene -> Transcripts
    gene_id = Field(Integer, foreign_key ="genes.id")

    gene: "Gene" = Relationship(back_populates="transcripts")

    # many to many Exons <-> Transcripts
    exons: List["Exon"] = Relationship(back_populates="transcripts", link_model = ExonTranscriptsLink)

    # many to many Repeats <-> Transcripts
    repeats: List["Repeat"] = Relationship(back_populates="transcripts", link_model = RepeatTranscriptsLink)

    def __repr__(self):
        return "Transcript(ensembl_transcript={}, start={}, end={})".format(
            self.ensembl_transcript,
            self.start,
            self.end
        )

class Gene(SQLModel, table=True):
    __tablename__ = "genes"
    __table_args__ = (UniqueConstraint("ensembl_version_id"), CheckConstraint("strand in ('+', '-')"))

    id: int = Field(default=None, primary_key=True)
    ensembl_id: str = Field(nullable=False)
    ensembl_version_id: str = Field(nullable=False)
    entrez_id: Optional[str] = Field(default=None)
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    chr: str = Field(nullable=False)
    strand: str = Field(nullable=False)
    start: int = Field(nullable=False)
    end: int = Field(nullable=False)    

    transcripts: List[Transcript] = Relationship(back_populates="gene")
    # Add relationship directive to Gene class for one to many Gene -> Repeats
    # repeats: List[Repeat] = Relationship(back_populates="gene")
    # many to many Gene <-> Repeat
    repeats: List["Repeat"] = Relationship(back_populates="genes", link_model = GenesRepeatsLink)

    def __repr__(self):
        return "Gene(ensembl_id={}, chr={}, strand={}, start={}, end={}, name={}, description={}, entrez_id={}, uniprot_id={})".format(
            self.ensembl_id,
            self.chr,
            self.strand,
            self.start,
            self.end,
            self.name,
            self.description,
            self.entrez_id
        )

class Exon(SQLModel, table=True):
    __tablename__ = "exons"
    __table_args__ = (UniqueConstraint("ensembl_exon"),)

    id: int = Field(default=None, primary_key=True)
    ensembl_exon: str = Field(nullable=False)
    start: int =Field(nullable=False)
    end: int = Field(nullable=False)
    cds: bool = Field(nullable=False)
    start_codon: int = Field(default=None)
    stop_codon: int = Field(default=None)

    # many to many Exons <-> Transcripts
    transcripts: List["Transcript"] = Relationship(back_populates="exons", link_model = ExonTranscriptsLink)

    def __repr__(self):
        return "Exon(ensembl_exon={}, start={}, end={}, cds={}, start_codon={}, stop_codon={})".format(
            self.ensembl_exon,
            self.start,
            self.end,
            self.cds,
            self.start_codon,
            self.stop_codon
        )





