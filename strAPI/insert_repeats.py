#!/usr/bin/env python3
import argparse
import os
import pickle

from tral.repeat_list.repeat_list import RepeatList

from repeats.models import Gene, Repeat
from gtf_to_sqlite import connection_setup
from utils.constants import UPSTREAM, CHROMOSOME_LENGTHS

def load_repeatlists(directory, targets=None):
    # collect all pickle files from input directory
    file_names = [i for i in os.listdir(directory) if i.endswith(".pickle")]

    if targets:
        if not isinstance(targets, (list, set, tuple)):
            raise ValueError("Specify files to include in a list, set or tuple")
        file_names = [i for i in file_names if i.replace(".pickle", "") in targets]

    for file_name in file_names:
        full_path = os.path.join(directory, file_name)

        with open(full_path, "rb") as f:
            repeat_list = pickle.load(f)

        # Double check to see if collected object is RepeatList
        if not isinstance(repeat_list, RepeatList):
            continue

        yield(file_name, repeat_list)

def get_gene_from_repeatlist(session, file_name, upstream=UPSTREAM):
    chromosome = file_name.split("_")[0]
    if not chromosome.startswith("chr"):
        raise Exception(f"Could not determine chromosome for repeatlist from {file_name}")

    gene_begin = int(file_name.split("_")[1].split("-")[0])
    gene_end = int(file_name.split("_")[1].split("-")[1])

    if "_fw" in file_name:
        strand = "fw"
        # also check begin - upstream, if > 1, get gene using both begin and end later
        ## if < 1, we have to try with only the end position        
        if gene_begin < 1:
            return session.query(Gene).filter_by(chromosome=chromosome, strand=strand, end=gene_end).one()        
        gene_begin += UPSTREAM
    elif "_rv" in file_name:
        strand = "rv"
        # also check end + upstream, if > chromosome length, get gene using both begin and end later
        ## if gene_end + promoter > chromosome length, we have to try with only the end position        
        if gene_end == CHROMOSOME_LENGTHS[chromosome]:
            gene = session.query(Gene).filter_by(chromosome=chromosome, strand=strand, begin=gene_begin).one()
            return gene
        gene_end -= UPSTREAM
    else:
        raise Exception(f"Could not determine strand for repeatlist from file {file_name}")
   
    return session.query(Gene).filter_by(chromosome=chromosome, strand=strand, begin=gene_begin, end=gene_end).one()

def add_repeat(gene, repeat, score_type, upstream=UPSTREAM):
    # repeat contains coordinates relative to the extracted genomic region that it was detected in.
    ## Thus, need to remap to chromosomal coordinates before adding to DB
    if gene.strand == "fw":
        region_begin = gene.begin - upstream
        if region_begin < 1:
            # The begin of the gene was closer to the start of the chromosome than the number of bases
            ## that were included as upstream 'promoter' region. Thus, the negative region begin value is
            ### reset to 1
            region_begin = 1
        chrom_begin = region_begin + repeat.begin - 1 # only valid for fw strand genes
    else:
        region_end = gene.end + upstream
        if region_end > CHROMOSOME_LENGTHS[gene.chromosome]:
            region_end = CHROMOSOME_LENGTHS[gene.chromosome]          
        repeat_end = repeat.begin + repeat.repeat_region_length - 1 
        chrom_begin = region_end - repeat_end + 1 # only valid for rv strand genes
    
    # Repeats where gappy units have been trimmed no longer have a '.TRD' attribute, set this to None
    ## in this case so it will show up as NULL in DB (or as unknown)
    if not hasattr(repeat, "TRD"):
        repeat.TRD = None

    # initialize instance of database Repeat
    db_repeat = Repeat(
        source = repeat.TRD,
        msa = ",".join(repeat.msa), # convert msa from list() to ',' separated str()
        begin = chrom_begin,
        end = chrom_begin + repeat.repeat_region_length - 1, # calculate end position
        l_effective = repeat.l_effective,
        n_effective = repeat.n_effective,
        region_length = repeat.repeat_region_length,
        score_type = score_type,
        score = repeat.d_score[score_type],
        p_value = repeat.d_pvalue[score_type],
        divergence = repeat.d_divergence[score_type]
    )


    # relate Repeat to gene
    gene.repeats.append(db_repeat)

    # relate Repeat to all Transcript(s) of the Gene where (partial) overlap exists
    for transcript in gene.transcripts:
        if db_repeat.begin >= transcript.begin and db_repeat.begin <= transcript.end:
            transcript.repeats.append(db_repeat)
        elif db_repeat.end <= transcript.end and db_repeat.end >= transcript.begin:
            transcript.repeats.append(db_repeat)

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path to where the repeat-containing database can be found"
    )
    parser.add_argument(
        "--repeat_dir", "-r", type=str, required=True, help="Path to directory where pickled, scored and filtered repeats are stored"
    )
    parser.add_argument(
        "--score_type", "-s", type=str, required=True, help="Which score type will be included in DB? options: phylo, phylo_gap01, phylo_gap001"
    )

    return parser.parse_args()


def main():
    args = cla_parser()
    db_path = args.database
    input_path = args.repeat_dir
    score_type = args.score_type
    
    engine, session = connection_setup(db_path)

    for file_name, repeat_list in load_repeatlists(input_path):
        if not file_name.endswith(".pickle"):
            continue
        # retrieve the Gene that the repeat_list belongs to
        try:
            #print(file_name)
            gene = get_gene_from_repeatlist(session, file_name)
            #print(gene)
        except Exception as e:
            print(file_name)
            print(e)
            exit(1)
            

        # make db entry for each repeat and add relationships to Gene and Transcripts
        for repeat in repeat_list.repeats:
            #print("Adding repeats")
            add_repeat(gene, repeat, score_type)
        session.commit()

if __name__ == "__main__":
    main()

