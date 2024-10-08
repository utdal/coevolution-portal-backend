#from celery import shared_task
import time
import os
import biotite
from typing import Union, TextIO, Literal
import tempfile
import gzip
import urllib.request
import biotite.structure
import numpy as np
import numpy.typing as npt

from dcatoolkit import DirectInformationData, ResidueAlignment, StructureInformation
from dcatoolkit import MSATools
import pyhmmer
#from dca.dca_class import dca

aa_alphabet = pyhmmer.easel.Alphabet.amino()

#alphabet used in production of MSAs and HMMs.
def generate_hmm_and_profiles(seed_sequence_filepath: str, seed_name: str) -> tuple:
    seed_MSA_fname = seed_sequence_filepath
    background = None
    hmm = None
    profile = None
    optimized_profile = None
    with pyhmmer.easel.MSAFile(seed_MSA_fname, digital=False, alphabet=aa_alphabet) as msa_fs:
        loaded_seed = msa_fs.read()
        if isinstance(loaded_seed, pyhmmer.easel.TextMSA):
            loaded_seed_text: pyhmmer.easel.TextMSA = loaded_seed
        else:
            raise TypeError("The seed sequence(s) provided are not in the format of a text MSA")
        # Must convert to a digital MSA according to https://pyhmmer.readthedocs.io/en/stable/examples/msa_to_hmm.html
        loaded_seed_digital = loaded_seed_text.digitize(alphabet=aa_alphabet)
        builder = pyhmmer.plan7.Builder(alphabet=aa_alphabet)
        background = pyhmmer.plan7.Background(alphabet=aa_alphabet)
        loaded_seed_digital.name = f"{seed_name}_MSA".encode()
        hmm, profile, optimized_profile = builder.build_msa(loaded_seed_digital, background)
    return background, hmm, profile, optimized_profile

def hmmsearch_from_seed(seed_sequence_filepath: str, seed_name: str):
    background, hmm, _, _ = generate_hmm_and_profiles(seed_sequence_filepath, seed_name)
    # Define a database path for hmmsearch to search through.
    database_path = "/mfs/io/groups/morcos/uniprot_db/uniprot_sprot_trembl.fasta"
    pipeline = pyhmmer.plan7.Pipeline(alphabet=aa_alphabet, background=background)
    hits = None
    with pyhmmer.easel.SequenceFile(database_path, digital=True, alphabet=aa_alphabet) as seq_file:
        hits = pipeline.search_hmm(hmm, seq_file)
    if hits:
        produced_msa: pyhmmer.easel.MSA = hits.to_msa(alphabet=aa_alphabet, digitize=False)
        if isinstance(produced_msa, pyhmmer.easel.TextMSA):
            return produced_msa
        else:
            raise TypeError("The produced MSA is not an MSA in text format.")

def filter_by_consecutive_gaps(input_filepath: str, output_filepath: str, max_gaps: int):
    input_MSA = MSATools.load_from_file(input_filepath)
    output_MSA = MSATools(input_MSA.filter_by_continuous_gaps(max_gaps))
    output_MSA.write(output_filepath)

def produce_alignment_to_protein(protein_sequence: str, seed_sequence_filepath: str, seed_name: str, protein_name: str):
    background, hmm, profile, optimized_profile = generate_hmm_and_profiles(seed_sequence_filepath, seed_name)
    protein_query = pyhmmer.easel.TextSequence(name=f"{protein_name}".encode(), sequence=protein_sequence).digitize(alphabet=aa_alphabet)
    hits = list(pyhmmer.hmmer.hmmscan(queries=protein_query, profiles=[hmm], background=background))
    # Queries refers to the protein sequence, which yields the target of the alignment.
    # Profiles refers to the domain's profile HMM generated from the domain / full protein's seed sequence. The same HMM used to generate an MSA.
    best_alignment = hits[0][0].best_domain.alignment
    return ResidueAlignment(best_alignment.hmm_name.decode(), best_alignment.target_name.decode(), best_alignment.target_from, best_alignment.hmm_from, best_alignment.hmm_sequence, best_alignment.target_sequence)

def get_mapped_residues(DI_arr: npt.NDArray, rcsb_pdb_id: str, seed_sequence_filepath, seed_name, protein_name):
    structure = StructureInformation.fetch_pdb(rcsb_pdb_id)
    res_align = produce_alignment_to_protein(structure.full_sequence, seed_sequence_filepath=seed_sequence_filepath, seed_name=seed_name, protein_name=protein_name)
    res_align = produce_alignment_to_protein(structure.non_missing_sequence, seed_sequence_filepath=seed_sequence_filepath, seed_name=seed_name, protein_name=protein_name)
    CISD3_DI_data = DirectInformationData.load_as_ndarray(DI_arr)
    mapped_CISD3_6avj = CISD3_DI_data.get_ranked_mapped_pairs(res_align, res_align, pairs_only=False)
    print(mapped_CISD3_6avj)

#produce_alignment_to_protein("GSMSIFTPTNQIRLTNVAVVRMKRAGKRFEIACYKNKVVGWRSGVEKDLDEVLQTHSVFVNVSKGQVAKKEDLISAFGTDDQTEICKQILTKGEVQVSDKERHTQLEQMFRDIATIVADKCVNPETKRPYTVILIERAMKDIHYSVKTNKSTKQQALEVIKQLKEKMKIERAHMRLRFILPVNEGKKLKEKLKPLIKVIESEDYGQQLEIVCLIDPGCFREIDELIKKETKGKGSLEVLNLKDVEEGDEKFE", "alt_dev/SBDS_domainC_seed.afa", "SBDS_domain_C", "2L9N")
#print(type(open("alt_dev/SBDS_domainC_seed.afa")))
"""
final_msa = hmmsearch_from_seed("CISD3_uniprot_seq.fasta", "CISD3")

msa_filepath = "output_MSA_CISD3.fasta"
filtered_msa_filepath = "output_MSA_CISD3_filtered_35.fasta"

with open(msa_filepath, 'wb') as fs:
    final_msa.write(fs, "afa")

filter_by_consecutive_gaps(msa_filepath, filtered_msa_filepath, 35)

#produce_alignment_to_protein()
# dca(filtered_msa_filepath)
"""
DI = np.array([[1,8,3.0],[5,15,8.0]])
get_mapped_residues(DI, "6AVJ", "alt_dev/CISD3_uniprot_seq.fasta", "CISD3", "6AVJ")