from operator import methodcaller
import sys
sys.path.append("..")

import argparse
from strAPI.repeats.models import TRPanel, Cohort, Genome
from gtf_to_sql import connection_setup

def make_db_trpanel(session, trpanel_info):

    # initialize instance of TR Panel object
    db_panel = TRPanel(
        name = trpanel_info['name'],
        method = trpanel_info['method']
    )

    # get corresponding genome and assign to panel
    genome = session.query(Genome).filter(Genome.name == trpanel_info['genome']).one()
    genome.trpanels.append(db_panel)
    db_panel.genome_id = genome.id

    return db_panel

def make_db_cohort(session, cohort_info):

    # initialize instance of TR Panel object
    db_cohort = Cohort(
        name = cohort_info['name'],  
    )

    # get corresponding genome and assign to panel
    trpanel = session.query(TRPanel).filter(TRPanel.name == cohort_info['panel']).one()
    #print(trpanel)
    trpanel.cohorts.append(db_cohort)
    db_cohort.trpanel_id = trpanel.id

    return db_cohort

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
    list_of_panels = [{'name': 'gangstr_hg38_ver16', 'method': 'GangSTR', 'genome': 'hg38'},
                       {'name': 'hipstr_hg19', 'method': 'HipSTR', 'genome': 'hg19'},
                       {'name': 'EnsembleTR',  'method':'HipSTR-GangSTR-adVNTR-ExpansionHunter', 'genome': 'hg38'},
                       {'name': 'gangstr_mm10', 'method': 'GangSTR', 'genome': 'mm10'},
                       {'name': 'hipstr_rn7', 'method': 'HipSTR', 'genome': 'rn7'},
                       {'name': 'gangstr_crc_hg38', 'method': 'GangSTR', 'genome': 'hg38'}
]
    
    for t in list_of_panels:
        t_obj = make_db_trpanel(session, t)
        session.add(t_obj)
    session.commit()

    list_of_cohorts = [{'name': 'Sinergia-CRC', 'panel': 'gangstr_crc_hg38'}, 
                       {'name': 'GTEx', 'panel': 'gangstr_hg38_ver16'},
                       {'name': '1000G-150', 'panel': 'hipstr_hg19'},
                       {'name': '1000G', 'panel': 'hipstr_hg38'},
                       {'name': 'GTEx', 'panel': 'hipstr_hg19'},
                       {'name': 'BXD', 'panel': 'gangstr_mm10'},
                       {'name': 'HS', 'panel': 'hipstr_rn7'}]

    for c in list_of_cohorts:
        c_obj = make_db_cohort(session, c)
        session.add(c_obj)
    session.commit()

if __name__ == "__main__":
    main()