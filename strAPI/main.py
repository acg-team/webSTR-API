from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from . import models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


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


@app.get("/genes/", response_model=List[schemas.Gene])
def show_genes(db: Session = Depends(get_db)):
    genes = db.query(models.Gene).all()
    return genes

@app.get("/repeats/", response_model=List[schemas.Repeat])
def show_genes(db: Session = Depends(get_db)):
    repeats = db.query(models.Repeat).all()
    return repeats