#!/bin/bash

db=/home/oxana/projects/str_database/db/str.db

echo "Setting up database file"

python3 setup_db.py --database $db

echo "Adding genes"
python3 gtf_to_sqlite.py --gtf /home/oxana/projects/str_database/data/genome_anntotation/gencode.v22.annotation.gtf -d $db

for i in {1..25..1}
    do
       echo "Adding part $i "
       python3 insert_repeats.py -d $db -r /home/oxana/projects/str_database/data/repeats/CRC_STRs/results/repeats/refined/part_$i -s phylo
done
