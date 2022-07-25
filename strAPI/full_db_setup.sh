#!/bin/bash
set -eou pipefail

#change password to yours before running
# db=postgresql+psycopg2://postgres:password@localhost:5432/strdb
# gtf="/home/oxana/projects/str_database/data/genome_anntotation/gencode.v22.annotation.gtf"
# db="sqlite:////Users/maxverbiest/PhD/projects/str_database/db/example.db"
gtf="/Users/maxverbiest/PhD/data/genome_annotations/gencode.v22.annotation.gtf"
repeat_dir="/Users/maxverbiest/PhD/projects/str_database/data/repeats"
# db="postgresql+psycopg2://postgres:Oxanaisnice@localhost:5432/strdb"
db="postgresql+psycopg2://postgres:postgres@localhost:5432/strdb"
echo "Setting up database file"
# python3 setup_db.py --database "${db}"

#echo "Adding genes"
# python3 gtf_to_sql.py --gtf "${gtf}" -d "${db}"

#echo "Inserting repeats"
python3 insert_repeats.py -d "${db}" -r "${repeat_dir}" -s phylo_gap01
