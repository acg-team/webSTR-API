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

    # one to many Genome -> Genes
    genome_id: int = Field(foreign_key ="genomes.id")
    genome: "Genome" = Relationship(back_populates="genes")

    transcripts: List[Transcript] = Relationship(back_populates="gene")
    # Add relationship directive to Gene class for one to many Gene -> Repeats
    # repeats: List[Repeat] = Relationship(back_populates="gene")
    # many to many Gene <-> Repeat
    repeats: List["Repeat"] = Relationship(back_populates="genes", link_model = GenesRepeatsLink)

    def __repr__(self):
        return "Gene(ensembl_id={}, chr={}, strand={}, start={}, end={}, name={}, description={}, entrez_id={})".format(
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

class CRCVariation(SQLModel, table=True):
    __tablename__ = "crcvariations"

    id: int = Field(primary_key=True)   
    instable_calls: Optional[int] = Field(default = None)
    stable_calls: Optional[int] = Field(default = None)
    total_calls: Optional[int] = Field(default = None)
    frac_variable: Optional[float] = Field(default = None)
    avg_size_diff: Optional[float] = Field(default=None)

    # One to one, Repeat - CRCVariation
    repeat_id: int = Field(foreign_key = "repeats.id")
    repeat: "Repeat" = Relationship(back_populates="crcvariation")
    

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

    # One to many, TRPanel -> Repeat
    trpanel_id: int = Field(foreign_key = "trpanels.id")
    trpanel: "TRPanel" = Relationship(back_populates="repeats")

    # Add relationship directive to Repeat class for one to one Repeat - CRCVariation
    #crcvariation : "CRCVariation" = Relationship(back_populates="repeat")
    crcvariation: Optional["CRCVariation"] = Relationship(
        sa_relationship_kwargs={'uselist': False},
        back_populates="repeat"
    )

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

""""
Cohorts or studies/experiments 

Combination of reference TRPanel + method + specific set of interesting STRs for 
which some calculations were then performed and saved in a database. 

Options: 1000G-150 (hg19, split by population), 1000G-HC (hg38, split by population and caller),
GTEx (hg19), BXD (mm10), HS (rn7), GTEx (hg38), Sinergia-CRC (hg38)
"""
class Cohort(SQLModel, table=True):
    __tablename__ = "cohorts"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    #cohort_set: Add a set of STRs, many to many relationship with Repeats or this is enough to handle in 
    # the resuts tables

    # one to many TRPanel -> Cohort
    trpanel_id: int = Field(foreign_key ="trpanels.id")
    trpanel: "TRPanel" = Relationship(back_populates="cohorts")

    def __repr__(self):
        return "Cohort(id={}, name={}, method={}, trpanel_id={})".format(
            self.id,
            self.name,
            self.trpanel_id
        )
""""
Reference Panels of STRs. Also known as TR SETS. 

Options: gangstr_hg38_ver16, hipstr_hg19, hipstr_hg38, gangstr_mm10, hipstr_rn7

Reference panel identifier - combination of method and genome assembly version
"""
class TRPanel(SQLModel, table=True):
    __tablename__ = "trpanels"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    method: str = Field(nullable=False)
    
    # one to many Genome -> TRPanel
    genome_id: int = Field(foreign_key ="genomes.id")
    genome: "Genome" = Relationship(back_populates="trpanels")

    # one to many TRPanel -> Cohorts 
    cohorts: List[Cohort] = Relationship(back_populates="trpanel")

    # one to many TRPanel -> Repeats 
    repeats: List[Repeat] = Relationship(back_populates="trpanel")

    def __repr__(self):
        return "TRPanel(id={}, name={}, method={}, genome_id={})".format(
            self.id,
            self.name,
            self.genome_id
        )
"""
Genome assembly versions 

"""
class Genome(SQLModel, table=True):
    __tablename__ = "genomes"

    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    organism: str = Field(nullable=False)
    version: str = Field(nullable=True)

    trpanels : List[TRPanel] = Relationship(back_populates="genome")
    genes : List[Gene] = Relationship(back_populates="genome")

    def __repr__(self):
        return "Genome(id={}, name={}, organism={})".format(
            self.id,
            self.name,
            self.organism
        )











