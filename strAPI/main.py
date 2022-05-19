import io
import csv
from typing import List, Optional

from fastapi.openapi.utils import get_openapi
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from fastapi.responses import StreamingResponse

from sqlmodel import Session, select 

from .repeats import models, schemas
from .repeats.database import get_db, engine

# this is not needed if using alembic
#models.Base.metadata.create_all(bind=engine)

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

@app.get("/")
def main():
    return RedirectResponse(url="/docs/")

# Get 100 genes (testing query)
@app.get("/genes/", response_model=List[schemas.Gene], tags=["Genes"])
def show_genes(db: Session = Depends(get_db)):
    genes = db.query(models.Gene).limit(100).all()
    return genes

""" 
Retrieve all repeats associated with a given gene
     
   Parameters
   gene (Gene):
        Ensembl id of a gene for which the repeats will be retrieved
   
    Returns
    List of Repeats
"""
@app.get("/repeats/", response_model=List[schemas.RepeatInfo], tags=["Repeats"])
def show_repeats(gene_names: List[str] = Query(None), ensembl_ids: List[str] = Query(None), download: Optional[bool] = False, db: Session = Depends(get_db)):  
    def repeats_to_list(repeats):
        rows = []
        for r in iter(repeats):
            repeat = r[0]
            gene = r[1]
            rows.append({
                "start":  repeat.start,
                "end":  repeat.end,
                "msa": repeat.msa,
                "l_effective": repeat.l_effective,
                "n_effective": repeat.n_effective,
                "ensembl_id": gene.ensembl_id,
                "chr": gene.chr,
                "strand": gene.strand,
                "gene_name": gene.name,
                "gene_desc": gene.description
            })
        return rows

    def repeats_to_csv(repeats):
        csvfile = io.StringIO()
        headers = ['gene','chr','start','end','msa','l_effective','n_effective']
        
        writer = csv.DictWriter(csvfile, headers)
        writer.writeheader()
        for row in repeats_to_list(repeats):
            writer.writerow(row)
        csvfile.seek(0)
        return(yield from csvfile)

    gene_obj_ids = []
    if gene_names:
        genes =  db.query(models.Gene).with_entities(models.Gene.id).filter(models.Gene.name.in_(gene_names)).all()
        gene_obj_ids = [id[0] for id in genes]

    elif ensembl_ids:
        genes =  db.query(models.Gene).with_entities(models.Gene.id).filter(models.Gene.ensembl_id.in_(ensembl_ids)).all()
        gene_obj_ids = [id[0] for id in genes]

    statement = select(models.Repeat, models.Gene, models.GenesRepeatsLink
        ).join(models.Gene).where(models.Gene.id == models.GenesRepeatsLink.gene_id
        ).join(models.Repeat).where(models.Repeat.id == models.GenesRepeatsLink.repeat_id
        ).filter(models.Gene.id.in_(gene_obj_ids))
        
    repeats = db.exec(statement)
    
    if download:
        return StreamingResponse(repeats_to_csv(repeats), media_type="text/csv")
    else:
        results = repeats_to_list(repeats)
        return results

""" 
Retrieve all variations given a repeat id 
     
   Parameters
   repeat (Repeat):
        repeat_id
   
    Returns
    List of Variations 
"""
#@app.get("/variations/", response_model=List[schemas.CRCVariation], tags=["Variations"])
#def show_variation(repeat_id: int, db: Session = Depends(get_db)):
#    variations = db.query(models.CRCVariation).filter(models.CRCVariation.repeat_id == repeat_id).all()
#    return variations


""" 
Retrieve all STR variations found in the genes associated with given gene names
     
   Parameters
   gene (Gene):
        Gene name
   
    Returns
    Streams a csv file of variations for the given gene
"""
@app.get("/variations/", response_model=List[schemas.CRCVariation], tags=["Variations"])
def show_str_variation_in_genes(gene_names: List[str] = Query(None), download: Optional[bool] = False, db: Session = Depends(get_db)):
    def variations_to_csv(variations):
        csvfile = io.StringIO()
        headers = ['patient','sample_type','repeat_id','start','end','ref','alt']
        rows = []
        for var in variations:
            rows.append(
                {
                    'patient': var.tcga_barcode,
                    'sample_type': var.sample_type,
                    'repeat_id': var.repeat_id,
                    'start': var.start,
                    'end': var.end,
                    'ref': var.reference,
                    'alt': var.alt
                }
            )
        writer = csv.DictWriter(csvfile, headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        csvfile.seek(0)
        return(yield from csvfile)
    
    genes =  db.query(models.Gene).with_entities(models.Gene.id).filter(models.Gene.name.in_(gene_names)).all()
    gene_ids = [id[0] for id in genes]
    repeats = db.query(models.Repeat).with_entities(models.Repeat.id).filter(models.Repeat.genes.any(
            models.GenesRepeatsLink.gene_id.in_(gene_ids))).all()
    repeat_ids = [id[0] for id in repeats]

    variations = db.query(models.CRCVariation).filter(models.CRCVariation.repeat_id.in_(repeat_ids)).all()

    if download:
        return StreamingResponse(variations_to_csv(variations), media_type="text/csv")
    else:
        return variations

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

    if transcript_obj.gene.strand == "+":
        return list(sorted(exons, key=lambda x : x.start))
    elif transcript_obj.gene.strand == "-":
        return list(sorted(exons, key=lambda x : x.start, reverse=True))
