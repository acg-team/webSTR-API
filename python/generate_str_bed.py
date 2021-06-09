#!/usr/bin/env python3

import argparse

from setup_db import Gene
from gtf_to_sqlite import connection_setup

def make_str_bed(session, output_file, autosomes=True):
    """ Veeery inefficient as we go per chromosome, then sort the Genes and then also
    sort the Repeats. However, it will result in a nicely ordered .bed file and this is likely only
    done once for a database
    """
    chromosomes = [f"chr{i}" for i in range(1, 23)]
    if not autosomes: # generate bed file only for autosomes? Or sex chromosomes and mitochondrial as well?
        chromosomes += ["chrX", "chrY", "chrM"]
    with open(output_file, "w") as o:
        for chrom in chromosomes: # iterate over all chromosomes
            chrom_genes = session.query(Gene).filter_by(chromosome=chrom).all()
            sorted_chrom_genes = list(sorted(chrom_genes, key=lambda x: x.begin))
            for gene in sorted_chrom_genes:
                repeats = list(sorted([repeat for repeat in gene.repeats], key=lambda x: x.begin))
            for repeat in repeats:
                line = "\t".join([
                    chrom, 
                    str(repeat.begin), 
                    str(repeat.end), 
                    str(repeat.l_effective), 
                    str(repeat.n_effective), 
                    str(repeat.id)])
                line += "\n"
                o.write(line)

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path to where the repeat-containing database can be found"
    )
    parser.add_argument(
        "--bed", "-b", type=str, required=True, help="Path to where the .bed file of repeats will be generated"
    )

    return parser.parse_args()

def main():
    args = cla_parser()
    db_path = args.database
    output_file = args.bed

    engine, session = connection_setup(db_path)

    make_str_bed(session, output_file, autosomes=True)      

if __name__ == "__main__":
    main()
