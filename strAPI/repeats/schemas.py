from datetime import date
from typing import Optional
from pydantic import BaseModel


class Gene(BaseModel):
    ensembl_gene: str
    chromosome: str
    strand: str
    begin: int
    end: int

    class Config:
        orm_mode = True


class Repeat(BaseModel):
    begin: int
    end: int 
    msa: str
    p_value: float

    class Config:
        orm_mode = True


class Transcript(BaseModel):
    begin: int
    end: int 
    ensembl_transcript: str 

    class Config:
        orm_mode = True

class Exon(BaseModel):
    ensembl_exon : str
    begin : int
    end : int
    cds : bool
    start_codon : Optional[int]
    stop_codon : Optional[int]

    class Config:
        orm_mode = True
