#!/usr/bin/env python3
import argparse
import os
import pickle
import sys 
sys.path.append("..")

from tral.repeat_list.repeat_list import RepeatList

from strAPI.repeats.models import Gene, Repeat, TRPanel
from gtf_to_sql import connection_setup
from strAPI.utils.constants import UPSTREAM, CHROMOSOME_LENGTHS

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

def repeat_in_element(repeat, element, upstream=None):
    region_start, region_end = element.start, element.end
    if upstream:
        if not isinstance(element, Gene):
            raise NotImplementedError("Including upstream region is currently only supported for Gene database entries")
        if element.strand == "+":
            region_start = max(region_start - UPSTREAM, 1)
        else:
            region_end = min(region_end + UPSTREAM, CHROMOSOME_LENGTHS[element.chr])

    repeat_end = repeat.begin + repeat.repeat_region_length - 1
    if region_start <= repeat.begin <= region_end:
        return True
    if region_start <= repeat_end <= region_end:
        return True
    return False

def make_db_repeat(repeat, score_type):
    if not hasattr(repeat, "TRD"):
        repeat.TRD = None

    # initialize instance of database Repeat
    db_repeat = Repeat(
        source = repeat.TRD,
        msa = ",".join(repeat.msa), # convert msa from list() to ',' separated str()
        start = repeat.begin,
        end = repeat.begin + repeat.repeat_region_length - 1, # calculate end position
        l_effective = repeat.l_effective,
        n_effective = repeat.n_effective,
        region_length = repeat.repeat_region_length,
        score_type = score_type,
        score = repeat.d_score[score_type],
        p_value = repeat.d_pvalue[score_type],
        divergence = repeat.d_divergence[score_type]
    )

    return db_repeat

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

    # Collect all genes from DB into dictionary (chromosomes as keys)
    gene_dict = dict()
    for gene in session.query(Gene).all():
        try:
            gene_dict[gene.chr].append(gene)
        except KeyError:
            gene_dict[gene.chr] = [gene]

    trpanel = session.query(TRPanel).filter(TRPanel.name == 'gangstr_crc_hg38').one()
    print(trpanel)

    for file_name, repeat_list in load_repeatlists(input_path):
        print(f"Inserting repeats from file '{file_name}'")
        repeat_chrom = file_name.split("_")[0]
        for repeat in repeat_list.repeats:
            gene_count = 0            
            for gene in gene_dict[repeat_chrom]:                
                if repeat_in_element(repeat=repeat, element=gene, upstream=UPSTREAM):
                    # The repeat could be mapped to a gene, check if this is the first 
                    # time the repeat maps to a gene (gene_count == 1), if so: make DB entry for repeat
                    gene_count += 1              
                    if gene_count == 1:                       
                        db_repeat = make_db_repeat(repeat, score_type)                                    
                    
                        # Add relationships to gene and tr panel 
                        gene.repeats.append(db_repeat)

                        db_repeat.trpanel_id = trpanel.id
                        trpanel.repeats.append(db_repeat)
                        

                    for transcript in gene.transcripts:
                        # Add repeat to all of the genes transcripts that it maps to
                        if repeat_in_element(repeat=repeat, element=transcript):
                            transcript.repeats.append(db_repeat)
            if gene_count == 0:
                print(f"WARNING: repeat {repeat} could not be mapped to any of the genes in the database")
    session.commit()

if __name__ == "__main__":
    main()
