from typing import List
from fastapi.openapi.utils import get_openapi
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from .repeats import models, schemas
from .repeats.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

description = """
Tral Short Tandem Repeats (STRs) database API 
"""

tags_metadata = [
    {
        "name": "Repeats",
        "description": "Retrieve all repeats associated with a given gene. You can query STRs using Ensembl ID.",
    },
    {
        "name": "Genes",
        "description": """ Here you'll find helper functions for working with genes, transcripts and exons. 
            You can retrieve all Exons associated with input Transcript and return in sorted order. 
            You can retrieve all Genes and all Transcripts for a given gene. """,
    },
]

app = FastAPI(
    contact={
        "name": "Oxana Lundström",
        "url": "http://merenlin.com",
        "email": "oxana@vild.ly",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
    redoc_url="/docs",
    docs_url=None
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="TralSTRs Database",
        version="0.0.1",
        description=description,
        routes=app.routes,
        tags=tags_metadata
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://www.sib.swiss//templates/sib/images/SIB_LogoQ_GBv.svg"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@app.get("/")
def main():
    return RedirectResponse(url="/docs/")

# Return all genes
@app.get("/genes/", response_model=List[schemas.Gene], tags=["Genes"])
def show_genes(db: Session = Depends(get_db)):
    genes = db.query(models.Gene).all()
    return genes

""" 
Retrieve all repeats associated with a given gene
     
   Parameters
   gene (Gene):
        Ensembl id of a gene for which the repeats will be retrieved
   
    Returns
    List of Repeats
"""
@app.get("/repeats/", response_model=List[schemas.Repeat], tags=["Repeats"])
def show_repeats(gene: str, db: Session = Depends(get_db)):
    gene_obj =  db.query(models.Gene).filter_by(ensembl_gene=gene).one()
    repeats = db.query(models.Repeat).filter_by(gene_id = gene_obj.id).all()
    return repeats


# for gene return all transcripts
@app.get("/transcript/{gene}", response_model=List[schemas.Transcript], tags=["Genes"])
def show_transcripts(gene: str, db: Session = Depends(get_db)):
    transcripts = db.query(models.Transcript).filter_by(ensembl_transcript=gene).all()
    return transcripts

""" Retrieve all Exons associated with input Transcript and return in sorted order. Option to
    filter on protein coding Exons only (add later)
    Parameters
    transcript (Transcript):
                Transcript for which the Exons will be retrieved
    protein (Bool):
                If True, only protein coding Exons will be returned

    Returns
    List of (filtered) Exons, sorted by order of appearance in the protein, so for Transcripts from the 
    reverse strand, order will be descending.
"""
@app.get("/exons/", response_model=List[schemas.Exon], tags=["Genes"])
def get_sorted_exons(transcript: str, protein: bool = False, db: Session = Depends(get_db)):
    exons = []
    transcript_obj =  db.query(models.Transcript).filter_by(ensembl_transcript=transcript).one()
    for exon in transcript_obj.exons:
        if protein and not exon.cds:
            continue
        exons.append(exon)

    if transcript_obj.gene.strand == "fw":
        return list(sorted(exons, key=lambda x : x.begin))
    elif transcript_obj.gene.strand == "rv":
        return list(sorted(exons, key=lambda x : x.begin, reverse=True))
