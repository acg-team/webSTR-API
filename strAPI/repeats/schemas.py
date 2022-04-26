from datetime import date
from typing import Optional
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


class Repeat(BaseModel):
    start: int
    end: int 
    msa: str
    l_effective: int
    n_effective: int
    divergence: float
    p_value: float

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

class Exon(BaseModel):
    ensembl_exon : str
    start : int
    end : int
    cds : bool
    start_codon : Optional[int]
    stop_codon : Optional[int]

    class Config:
        orm_mode = True
