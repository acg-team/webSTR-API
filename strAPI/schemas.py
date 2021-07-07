from datetime import date
from pydantic import BaseModel


class Gene(BaseModel):
    ensembl_gene: str
    chromosome: str
    strand: str
    begin: int
    end: int

    class Config:
        orm_mode = True