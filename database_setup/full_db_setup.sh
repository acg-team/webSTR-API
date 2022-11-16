#!/bin/bash
set -eou pipefail


gtf="../data/genome_anntotation/gencode.v22.annotation.gtf"
repeat_dir="../data/repeats"

#change password to yours before running
db=postgresql+psycopg2://postgres:password@localhost:5432/strdb

#echo "Setting up database file"
#python setup_db.py --database "${db}"

#echo "Adding genomes"
#python add_genomes.py -d "${db}"

#echo "Adding panels and cohorts"
#python add_panels_and_cohorts.py -d "${db}"

echo "Adding genes"
python gtf_to_sql.py --gtf "${gtf}" -d "${db}" -a "GRCh38.p2"

echo "Inserting repeats"
python insert_repeats.py -d "${db}" -r "${repeat_dir}" -s phylo_gap01

#echo "Inserting locus level variation"
#python update_repeats.py -d "${db}" -v data/20220527_locus_variation_no_groups.csv 
