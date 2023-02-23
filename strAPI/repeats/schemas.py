from datetime import date
from typing import Optional, List, Tuple
from pydantic import BaseModel


class Gene(BaseModel):
    ensembl_id: str
    chr: str
    strand: str
    start: int
    end: int
    name: Optional[str]
    description: Optional[str]

    class Config:
        orm_mode = True

class Exon(BaseModel):
    ensembl_exon : str
    start : int
    end : int
    cds : bool
    start_codon : Optional[int]
    stop_codon : Optional[int]

    class Config:
        orm_mode = True

class GeneInfo(BaseModel):
    ensembl_id: str
    chr: str
    strand: str
    start: int
    end: int
    name: Optional[str]
    description: Optional[str]
    exons: List[Exon]
    class Config:
        orm_mode = True

class Repeat(BaseModel):
    chr: str
    start: int
    end: int 
    msa: str
    motif: str
    l_effective: int
    n_effective: int
    divergence: float
    p_value: float

    class Config:
        orm_mode = True

class RepeatInfo(BaseModel):
    repeat_id: int
    chr: str
    start: int
    end: int
    msa: Optional[str]
    motif: str
    period: int
    copies: int
    ensembl_id: Optional[str]
    strand: Optional[str]
    gene_name: Optional[str]
    gene_desc: Optional[str]
    total_calls: Optional[int]
    frac_variable: Optional[float]
    avg_size_diff: Optional[float]

    class Config:
        orm_mode = True

class AlleleFrequency(BaseModel):
    population: str
    n_effective: int
    frequency: float
    het: float
    num_called: int
    repeat_id: int

    class Config:
        orm_mode = True

class CRCVariation(BaseModel):
    tcga_barcode: str
    sample_type: str
    start: int
    end: int
    reference: int
    alt: int
    repeat_id: int

    class Config:
        orm_mode = True

class Transcript(BaseModel):
    start: int
    end: int 
    ensembl_transcript: str 

    class Config:
        orm_mode = True


