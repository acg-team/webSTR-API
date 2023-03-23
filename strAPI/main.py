import os
import io
import csv
from . import genes as gn

from typing import List, Optional

from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi import Depends, FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from fastapi.responses import StreamingResponse

from sqlmodel import Session, select 
from sqlalchemy import nullslast

from .repeats import models, schemas
from .repeats.database import get_db, engine

# this is not needed if using alembic
#models.Base.metadata.create_all(bind=engine)

description = """
WebSTR-API: Database of Human genome-wide variation in Short Tandem Repeats (STRs) 
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
    swagger_ui_parameters={"syntaxHighlight.theme": "nord", 
                           "layout": "BaseLayout"},
    docs_url=None
)

app.mount("/static", StaticFiles(directory="static"), name="static")

lable_lang_mapping = {"Python": "Python"}

def add_examples(openapi_schema: dict, docs_dir):
    path_key = 'paths'
    code_key = 'x-codeSamples'

    for folder in os.listdir(docs_dir):
        base_path = os.path.join(docs_dir, folder)
        files = [f for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))]
        for f in files:
            parts = f.split('-')
            if len(parts) >= 2:
                route = '/' + '/'.join(parts[:-1])
                method = parts[-1].split('.')[0]
                print(f'[{path_key}][{route}][{method}][{code_key}]')

                if route in openapi_schema[path_key]:
                    if code_key not in openapi_schema[path_key][route][method]:
                        openapi_schema[path_key][route][method].update({code_key: []})

                    openapi_schema[path_key][route][method][code_key].append({
                        'lang': lable_lang_mapping[folder],
                        'source': open(os.path.join(base_path, f), "r").read(),
                        'label': folder,
                    })
            else:
                print(f'Error in adding examples code to openapi {f}')

    return openapi_schema

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="WebSTR API",
        version="1.0.1",
        description=description,
        routes=app.routes,
        tags=tags_metadata
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "/static/images/logo.png"
    }
    
    app.openapi_schema = add_examples(openapi_schema, '/static/examples/')
    # Disable code examples for now, path doesn't work
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
    gene_names = ["MSH6", "CDK12", "CTCF", "PAK1", "KRAS", "PMS2", "MLH1", "MSH2" , "BAX", "MSH3", "TGFBR1"]
    genes = db.query(models.Gene).filter(models.Gene.name.in_(gene_names)).all()
    return genes

""" 
    Retrieve gene information based on gene names 

    Returns
    List of Genes

    TODO: 
    - Add querying by ensembl id and by region coordinates 
    - Add features flag and return corresponding transcripts and exons
""" 
@app.get("/gene/", response_model=List[schemas.Gene], tags=["Genes"])
def show_genes(db: Session = Depends(get_db), gene_names: List[str] = Query(None), ensembl_ids: List[str] = Query(None), reqion_query: str = Query(None)):
    return gn.get_gene_info(db, gene_names, ensembl_ids, reqion_query)
    

@app.get("/genefeatures/", response_model=List[schemas.GeneInfo], tags=["Genes"])
def show_gene_info(db: Session = Depends(get_db), gene_names: List[str] = Query(None), ensembl_ids: List[str] = Query(None), reqion_query: str = Query(None)):
        genes = gn.get_gene_info(db, gene_names, ensembl_ids, reqion_query)
        return gn.get_genes_with_exons(db, genes)


""" 
Retrieve allele frequencies for the given repeat id 
     
   Parameters
   repeat (Repeat):
        repeat_id
   
    Returns
    List of Allele Frequencies
"""
@app.get("/allfreqs/", response_model=List[schemas.AlleleFrequency], tags=["Repeats"])
def show_allele_freqs(repeat_id: int, db: Session = Depends(get_db)):
    allfreqs = db.query(models.AlleleFrequency).filter(models.AlleleFrequency.repeat_id == repeat_id).all()
    #if allfreqs == []:
    #    return []
    return allfreqs

""" 
Retrieve repeat info given a repeat id 
     
   Parameters
   repeat (Repeat):
        repeat_id
   
    Returns
    Repeat info 
"""
@app.get("/repeatinfo/", response_model=schemas.RepeatInfo, tags=["Repeats"])
def show_repeat_info(repeat_id: int, db: Session = Depends(get_db)):
    repeat = db.query(models.Repeat).filter(models.Repeat.id == repeat_id).one_or_none()

    # Get CRC Variation associated with this repeat if available
    crcvar = db.query(models.CRCVariation).filter(models.CRCVariation.repeat_id == repeat_id).first()

    if crcvar is None:
        crcvar_info = dict(total_calls=None, frac_variable = None, avg_size_diff = None)
    else: 
        crcvar_info = dict(crcvar)
 
    # Get genes associated with this repeat
    statement = select(models.GenesRepeatsLink, models.Gene     
    ).where(models.GenesRepeatsLink.repeat_id == repeat_id 
    ).join(models.Gene).where(models.Gene.id == models.GenesRepeatsLink.gene_id) 
    gene = db.exec(statement).first()
    
    if gene is not None:
        gene_info = dict(gene[1])
    else:
        gene_info = {'ensembl_id': None, 'strand': None, 'name': None, 'description': None}
    print(gene_info)
    repeat_info = {
        "repeat_id": repeat.id,
        "chr": repeat.chr,
        "start":  repeat.start,
        "end":  repeat.end,
        "msa": repeat.msa,
        "motif": repeat.motif,
        "period": repeat.l_effective,
        "copies": repeat.n_effective,
        "ensembl_id": gene_info["ensembl_id"],
        "strand": gene_info["strand"],
        "gene_name": gene_info["name"],
        "gene_desc": gene_info["description"],
        "total_calls": crcvar_info["total_calls"],
        "frac_variable": crcvar_info["frac_variable"],
        "avg_size_diff": crcvar_info["avg_size_diff"]
    }

    return repeat_info


""" 
Retrieve all repeats associated with a given gene
     
   Parameters
   gene (Gene):
        Ensembl id of a gene for which the repeats will be retrieved
   
    Returns
    List of Repeats
"""
#TODO: Test on an example when there are multiple genes associated with the repeat
@app.get("/repeats", response_model=List[schemas.RepeatInfo], tags=["Repeats"])
def show_repeats(gene_names: List[str] = Query(None), ensembl_ids: List[str] = Query(None), region_query: str = Query(None), download: Optional[bool] = False, db: Session = Depends(get_db)):  
    def repeats_to_list(repeats):
        rows = []
        
        for r in iter(repeats):
            print(r)
            repeat = r[0]
            gene = r[1]
            if r[3]:
                crcvar = dict(r[3])
            else:
                crcvar = dict(total_calls=None, frac_variable = None, avg_size_diff = None)
    
            rows.append({
                "repeat_id": repeat.id,
                "chr": repeat.chr,
                "start":  repeat.start,
                "end":  repeat.end,
                "msa": repeat.msa,
                "motif": repeat.motif,
                "period": repeat.l_effective,
                "copies": repeat.n_effective,
                "ensembl_id": gene.ensembl_id,
                "strand": gene.strand,
                "gene_name": gene.name,
                "gene_desc": gene.description,
                "total_calls": crcvar["total_calls"],
                "frac_variable": crcvar["frac_variable"],
                "avg_size_diff": crcvar["avg_size_diff"]
            })
        return rows

    def repeats_to_csv(repeats):
        csvfile = io.StringIO()
        headers = ['repeat_id','chr','start','end','msa','motif','motif', 'period','copies', 
            'ensembl_id', 'strand','gene_name','gene_desc', 'total_calls',
             'frac_variable', 'avg_size_diff']
        
        writer = csv.DictWriter(csvfile, headers)
        writer.writeheader()
        for row in repeats_to_list(repeats):
            writer.writerow(row)
        csvfile.seek(0)
        return(yield from csvfile)

    # Retrieving things based on genes when gene_names
    if not region_query:
        genes = gn.get_gene_info(db, gene_names, ensembl_ids, region_query)
        gene_obj_ids = [gene.id for gene in genes]
        
        statement = select(models.Repeat, models.Gene, models.GenesRepeatsLink, models.CRCVariation     #SELECT genes, repeats, genes_repeats FROM ((genes_repeats
            ).join(models.Gene).where(models.Gene.id == models.GenesRepeatsLink.gene_id  #INNER JOIN genes ON genes.id = genes_repeats.gene_id)
            ).join(models.Repeat).where(models.Repeat.id == models.GenesRepeatsLink.repeat_id #INNER JOIN repeats on repeats.id = genes_repeats.repeat_id)
            ).filter(models.Gene.id.in_(gene_obj_ids)
            ).join(models.CRCVariation, isouter=True 
            ).order_by(nullslast(models.CRCVariation.frac_variable.desc())).order_by(models.CRCVariation.total_calls)
    
        repeats = db.exec(statement)
    else:
        region_split = region_query.split(':')
        chrom = 'chr' + region_split[0]
        coord_split = region_split[1].split('-')
        start = int(coord_split[0])
        end = int(coord_split[1])
        #buf = int((end-start)*(GENEBUFFER))
        #start = start-buf
        #end = end+buf
   
        statement = select(models.Repeat, models.Gene, models.GenesRepeatsLink, models.CRCVariation     #SELECT genes, repeats, genes_repeats FROM ((genes_repeats
            ).join(models.Gene).where(models.Gene.id == models.GenesRepeatsLink.gene_id    
            ).join(models.Repeat).where(models.Repeat.id == models.GenesRepeatsLink.repeat_id #INNER JOIN repeats on repeats.id = genes_repeats.repeat_id)
            ).filter(models.Repeat.chr == chrom, models.Repeat.start >= start, models.Repeat.end <= end  
            ).join(models.CRCVariation).where(models.Repeat.id == models.CRCVariation.repeat_id  
            ).order_by(nullslast(models.CRCVariation.frac_variable.desc())).order_by(models.CRCVariation.total_calls)
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
    return genes.get_exons_by_transcript(db, protein, transcript)

