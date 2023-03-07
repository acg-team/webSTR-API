from . repeats.models import Gene, Transcript

GENEBUFFER = 0.1

def get_exons_by_transcript(db, cds_only, transcript_obj):
    exons = []
    for exon in transcript_obj.exons:
        if cds_only and not exon.cds:
            continue
        exons.append(exon)
    
    if transcript_obj.gene.strand == "+":
        return list(sorted(exons, key=lambda x : x.start))
    elif transcript_obj.gene.strand == "-":
        return list(sorted(exons, key=lambda x : x.start, reverse=True))

def get_gene_info(db, gene_names, ensembl_ids, reqion_query):
    genes = []
    if gene_names:
        genes = db.query(Gene).filter(Gene.name.in_(gene_names)).all()
    elif ensembl_ids:
        genes =  db.query(Gene).with_entities(Gene.id).filter(Gene.ensembl_id.in_(ensembl_ids)).all()  
    # Example chr1:182393-1014541
  
    elif reqion_query: 
        region_split = reqion_query.split(':')
        chrom = 'chr' + region_split[0]
        coord_split = region_split[1].split('-')
        start = int(coord_split[0])
        end = int(coord_split[1])
        buf = int((end-start)*(GENEBUFFER))
        start = start-buf
        end = end+buf
   
        genes = db.query(Gene).where(Gene.chr == chrom,Gene.start >= start,Gene.end <= end).all()
    
    return genes

def get_genes_with_exons(db, genes):
    genes_exons = []
    # TODO: change to for each transcript in transcripts...., right now only returns the first
    for gene in iter(genes):
        transcript = db.query(Transcript).filter_by(gene_id=gene.id).first()
        exons_obj = get_exons_by_transcript(db, True, transcript)
        exons = []
        for exon in iter(exons_obj):
            exons.append({
                "ensembl_exon": exon.ensembl_exon,
                "start":  exon.start,
                "end":  exon.end,
                "cds": exon.cds
            })
       
        genes_exons.append({
            "ensembl_id": gene.ensembl_id,
            "start":  gene.start,
            "end":  gene.end,
            "chr": gene.chr,
            "strand": gene.strand,
            "name": gene.name,
            "description": gene.description,
            "exons": exons
        })
        
        return genes_exons         
