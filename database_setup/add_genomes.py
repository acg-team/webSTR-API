import sys
sys.path.append("..")

import argparse
from strAPI.repeats.models import Genome
from gtf_to_sql import connection_setup

def make_db_genome(genome_info):

    # initialize instance of Genome object
    db_genome = Genome(
        name = genome_info['name'],
        organism = genome_info['organism'],
        version = genome_info['version']
    )
    
    return db_genome

def cla_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--database", "-d", type=str, required=True, help="Path to where the repeat-containing database can be found"
    )
   
    return parser.parse_args()

def main():
    args = cla_parser()
    db_path = args.database
    
    engine, session = connection_setup(db_path)

    list_of_genomes = [{'name': 'hg19', 'version': '', 'organism': 'Homo Sapiens'},
                       {'name': 'hg38', 'version': 'GRCh38.p2', 'organism': 'Homo Sapiens'},
                       {'name': 'mm10', 'version': '', 'organism': 'Mus Musculus'},
                       {'name': 'rn7', 'version': '', 'organism': 'Rattus norvegicus'}]
    
    for g in list_of_genomes:
        existing_genome = session.query(Genome).filter(Genome.name == g["name"]).first()
        if not existing_genome:
            g_obj = make_db_genome(g)
            session.add(g_obj)
    session.commit()

if __name__ == "__main__":
    main()