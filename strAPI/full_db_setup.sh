#!/bin/bash
set -eou pipefail

#change password to yours before running
# db=postgresql+psycopg2://postgres:password@localhost:5432/strdb
# gtf="/home/oxana/projects/str_database/data/genome_anntotation/gencode.v22.annotation.gtf"
db="sqlite:////Users/maxverbiest/PhD/projects/str_database/db/test.db"
gtf="/Users/maxverbiest/PhD/projects/str_database/data/genome_anntotation/chr1_small_gencode.v22.annotation.gtf"

echo "Setting up database file"

python3 setup_db.py --database "${db}"

echo "Adding genes"
python3 gtf_to_sql.py --gtf "${gtf}" -d "${db}"

# for i in {1..25..1}
#     do
#        echo "Adding part $i "
#        python3 insert_repeats.py -d $db -r /home/oxana/projects/str_database/data/repeats/CRC_STRs/results/repeats/refined/part_$i -s phylo
# done
