from celery import shared_task
import time
import os
from typing import Union, TextIO, Literal
import tempfile

import pyhmmer
from dca.dca_class import dca

@shared_task
def get_msa_task(seq):
    time.sleep(10)
    return seq + "\nabc\ndef\nAdditional sequences..."

@shared_task
def get_DI_pairs_task(msaPath):
    protein_family = dca(msaPath)
    protein_family.mean_field()
    os.remove(msaPath)
    return [(int(i), int(j), float(h)) for i, j, h in protein_family.DI]

@shared_task
def hmmsearch_from_seed(seed_sequence: Union[str, TextIO], protein_name: str, max_gaps: int=10000):
    #alphabet used in production of MSAs and HMMs.
    aa_alphabet = pyhmmer.easel.Alphabet.amino()
    # If a real HMM profile is found, seed sequence is ignored. Otherwise, it is required.

    # Supply a name for your HMM profile, regardless of whether you're building it or have one in your file system.
    hmm_prof_fname = f"{protein_name}_HMM"
    # Supply a name for your seed sequence. This is optional if you wish to search with an already produced profile HMM.
    #seed_seq_fname = f"{protein_name}.fasta"
	
    if type(seed_sequence) == str:    
        tmp = tempfile.NamedTemporaryFile()
        # Open the file for writing.
        tmp.name = ""
        with open(tmp.name, 'w') as f:
            f.write(seed_sequence)
        MSA_fname = tmp.name
    else:
        MSA_fname = seed_sequence

    # Define a database path for hmmsearch to search through.
    database_path = "/mfs/io/groups/morcos/uniprot_db/uniprot_sprot_trembl.fasta"

    # Remove intermediate .sto and .afa files.
    remove_intermediates=True

    # Check to see if max_gaps is a valid number >= 0.
    if max_gaps.isnumeric():
        max_gaps = int(max_gaps)

	#/mfs/io/groups/morcos/g1petastore_transfer/share/hmmer/bin/hmmbuild $hmm_prof_fname $seed_seq_fname > /dev/null 2>&1
    with pyhmmer.easel.MSAFile(MSA_fname, digital=False, alphabet=aa_alphabet) as msa_fs:
        loaded_seed: pyhmmer.easel.TextMSA = msa_fs.read()
        # Must convert to a digital MSA according to https://pyhmmer.readthedocs.io/en/stable/examples/msa_to_hmm.html
        loaded_seed = loaded_seed.digitize(alphabet=aa_alphabet)
        builder = pyhmmer.plan7.Builder(alphabet=aa_alphabet)
        background = pyhmmer.plan7.Background(alphabet=aa_alphabet)
        loaded_seed.name = f"{protein_name}_MSA"
        hmm, _, _ = builder.build_msa(loaded_seed, background)
    
    #The profile exists. We can now do hmmsearch.
    pipeline = pyhmmer.plan7.Pipeline(alphabet=aa_alphabet, background=background)
    with pyhmmer.easel.SequenceFile("", digital=True, alphabet=aa_alphabet) as seq_file:
        hits = pipeline.search_hmm(hmm, seq_file)
    ali = hits[0].domains[0].alignment
    print(ali)
    
    produced_msa = hits.to_msa(alphabet=aa_alphabet)
