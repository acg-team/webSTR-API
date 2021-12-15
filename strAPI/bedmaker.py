#!/usr/bin/env python3
import argparse
from collections import Counter

import numpy as np

from setup_db import Gene, Repeat
from gtf_to_sql import connection_setup

class BedMaker(object):      
    # Default threshold values for STRs, taken from Lai & Sun, 2003
    # format: {unit length: minimal number of units}
    default_thresholds = {
        1: 9, 
        2: 4,
        3: 4,
        4: 4,
        5: 4,
        6: 4
    }
    # All allowed values for chromosomes
    allowed_chromosomes = {f"chr{i}" for i in range(1, 23)}.union({"chrX", "chrY", "chrM"})
   
    def __init__(self, 
                db_session, 
                consensus_only: bool=False, 
                thresholds: dict=default_thresholds,
                chromosomes=allowed_chromosomes):
        self.db_session = db_session   
        self.consensus_only = consensus_only
        self.set_thresholds(thresholds)
        self.set_chromosomes(chromosomes)
        self.gene_selection = None

    def set_thresholds(self, thresh_dict: dict) -> None:
        # Check if all keys and values in supplied dictionary are integers
        if not all(isinstance(i, int) for i in [*thresh_dict.keys(), *thresh_dict.values()]):
            raise ValueError("Thresholds must be specified as dict(int(unit_len): int(min_units))")
        self.thresholds = thresh_dict

    def set_chromosomes(self, target_chromosomes) -> None:
        if not isinstance(target_chromosomes, (list, set, tuple)):
            raise ValueError("Specify target chromosomes as iterable")
        if not all(chrom in self.allowed_chromosomes for chrom in target_chromosomes):
            raise ValueError("Unrecognized target chromosome specified")
        self.chromosomes = target_chromosomes

    def set_gene_selection(self):
        gene_selection = dict()
        for chrom in self.chromosomes:
            for gene in self.db_session.query(Gene).filter_by(chr=chrom).all():
                gene_selection[gene.ensembl_id] = gene
        self.gene_selection = gene_selection

    def threshold_filter(self):
        """ Generator function that yields repeats containing a sequence of consecutive 
        perfect units longer than the predefined thresholds in self.thresholds

        Returns
        bed_tr (BedTR)          Representation of STR that passes threshold filters and
                                can be added to bed file                 
        """
        if not self.gene_selection:
            raise AttributeError("Gene selection needs to be set before bed file can be generated")
        seen_repeats = set()
        for gene in self.gene_selection.values():
            for repeat in gene.repeats:
                if repeat.id in seen_repeats:
                    continue
                seen_repeats.add(repeat.id)
                bed_tr_list = self.get_bed_trs(repeat, gene.chr)
                for bed_tr in bed_tr_list:
                    if self.consensus_only:
                        bed_tr_len = bed_tr.longest_cs
                    else:
                        bed_tr_len = len(bed_tr.units)
                    try:                                                         
                        if bed_tr_len >= self.thresholds[len(bed_tr.consensus_unit)]:
                            yield bed_tr
                    except KeyError:
                        # repeat.l_effective is not part of the self.threshold range currently active
                        continue

    def send_to_bed(self) -> None:
        """ Print string representations of STRs that pass the threshold filters
        to stdout
        """
        for bed_tr in self.threshold_filter():            
            print(bed_tr.get_bed_line())

    def get_consensus_unit(self, msa: str) -> str:    
        """ Given a comma-separated set of units representing a multiple sequence
        alignment (from DB), determine the consensus nt at each column of the alignment and 
        return the consensus unit. Insertion columns where the number of 
        insertions >= number of nucleotides are skipped. For each column, most common nt
        is selected as consensus, in case of tie: pick the first one in the list.

        Parameters
        msa (str):  String representation of a multiple sequence alignment, with units
                    delimited by commas
        
        Returns  
        consensus_unit (str): 
                    A consensus unit derived from the provided msa
        """    
        # Convert msa into list of lists, convert into np.Array() and transpose
        msa_matrix_t = np.array([list(unit) for unit in msa.split(",")]).transpose()
        consensus_unit = ""

        for msa_col in msa_matrix_t:
            # if half or more of the msa column are gap entries, skip column
            if np.count_nonzero(msa_col == '-') >= 0.5 * len(msa_col):
                continue

            # discard gap entries, get most common nt
            msa_col = msa_col[msa_col != '-']
            consensus_unit += Counter(msa_col).most_common(1)[0][0] # most_common() will return e.g. [('A': 5)]

        return consensus_unit

    def get_bed_trs(self, db_repeat, chromosome):
        """ Get all stretches of units with len == len(consensus_unit) from the input db_repeat. Will even
        return BedTRs of a single unit and leave all filtering up to the calling function.

        Parameters
        db_repeat:       A repeat region as represented in the database.

        Returns
        max_stretch (BedTR):
                        BedTR instance describing the longest sequence of units with the same length as
                        the consensus unit (though not necessarily perfect matches) found in the repeat region. 
        """
        consensus_unit = self.get_consensus_unit(db_repeat.msa)
        bed_tr_list = []
        current_bed_tr = BedTR(chromosome, consensus_unit, db_repeat.id, out_format="GangSTR")
        current_pos = db_repeat.start

        for unit in db_repeat.msa.split(","):            
            current_unit = unit.replace("-", "")
            if len(current_unit) == len(consensus_unit):    # current unit must be same length as consensus to be considered
                # if we only allow perfect units, check if current unit is a match. If not: reset
                if self.consensus_only and not current_unit == consensus_unit:
                    if len(current_bed_tr.units) > 0:
                        bed_tr_list.append(current_bed_tr)
                    current_bed_tr = BedTR(chromosome, consensus_unit, db_repeat.id, out_format="GangSTR")
                    current_pos += len(current_unit)
                    continue
                if len(current_bed_tr.units) == 0:
                    current_bed_tr.start = current_pos
                current_bed_tr.units.append(current_unit)
            else:
                if len(current_bed_tr.units) > 0:
                    bed_tr_list.append(current_bed_tr)
                current_bed_tr = BedTR(chromosome, consensus_unit, db_repeat.id, out_format="GangSTR")
            current_pos += len(current_unit)

        # Check if last entry in bed_tr_list equals the current_bed_tr
        if len(current_bed_tr.units) > 0:
            try:
                if current_bed_tr != bed_tr_list[-1]:
                    bed_tr_list.append(current_bed_tr)
            except IndexError:
                bed_tr_list.append(current_bed_tr)

        for bed_tr in bed_tr_list:
            if len(bed_tr.units) == 0:
                # No unit in the repeat matched the consensus unit, set end position to begin
                bed_tr.end = bed_tr.start
                continue
            # calculate end position of the longest stretch, set purity metric
            bed_tr.end = bed_tr.start + len(consensus_unit) * len(bed_tr.units) - 1
            bed_tr.set_purity()
            bed_tr.set_longest_cs_stretch()

        return bed_tr_list


class BedTR(object):   
    supported_formats =  {"GangSTR"}

    def __init__(self, chromosome: str, consensus_unit: str, db_tr: int, out_format: str) -> None:
        self.chromosome = chromosome
        self.consensus_unit = consensus_unit
        self.db_tr = db_tr
        self.set_out_format(out_format)
        self.units = []
        self.start = None
        self.end = None
        self.purity = None
        self.longest_cs = None

    def set_out_format(self, new_format: str) -> None:
        if not new_format in self.supported_formats:
            raise ValueError(f"Specified output format '{new_format}' is not supported")
        self.out_format = new_format

    def get_bed_line(self) -> str:
        if self.out_format == "GangSTR":
            return "\t".join([
                        str(self.chromosome),
                        str(self.start),
                        str(self.end),                    
                        str(len(self.consensus_unit)),
                        str(self.consensus_unit),
                        ".", # GangSTR allows for optional 6th col with off-target regions. Just placeholder '.' here for now
                        f"{self.db_tr}:{','.join(self.units)}:{self.purity}:{self.longest_cs}", # custom info field linking bed entry to DB
                    ])

    def set_purity(self):
        tr_seq_len = 0
        n_mismatches = 0
        for unit in self.units:
            tr_seq_len += len(unit)
            for idx, nt in enumerate(unit):
                if not nt == self.consensus_unit[idx]:
                    n_mismatches += 1
        self.purity = round(1 - (n_mismatches / tr_seq_len), 2)

    def set_longest_cs_stretch(self):
        if self.purity == 1.0:
            self.longest_cs = len(self.units)
            return
        cur_stretch = 0
        longest_stretch = 0
        for unit in self.units:            
            if unit == self.consensus_unit:                
                cur_stretch += 1
                if cur_stretch > longest_stretch:
                    longest_stretch = cur_stretch
                continue
            cur_stretch = 0
        self.longest_cs = longest_stretch
        
    def __str__(self):
        return f"BedTR from repeat '{self.db_tr}': {self.units}"

    def __eq__(self, other):
        if not isinstance(other, BedTR):
            return False
        if not self.db_tr == other.db_tr:
            return False
        if not self.start == other.start:
            return False
        if not self.end == other.end:
            return False
        if not self.consensus_unit == other.consensus_unit:
            return False
        return True
    
    def __ne__(self, other):
        return not self.__eq__(other)

def parse_cla():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d", "--database", type=str, required=True, help="Path to database for which .bed file will be generated"
    )
    parser.add_argument(
        "-p", "--perfect", action='store_true', help="True/False flag to control whether only perfect STRs will be considered (default: False)"
    )

    return parser.parse_args()



def main():
    args = parse_cla()
    
    engine, session = connection_setup(args.database)
    bedmaker = BedMaker(db_session=session, consensus_only=args.perfect)
    thresholds = {
        1: 9,
        2: 4,
        3: 4,
        4: 3,
        5: 3,
        6: 3
    }
    bedmaker.set_thresholds(thresholds)
    bedmaker.set_gene_selection()

    bedmaker.send_to_bed()

if __name__ == "__main__":
    main()
