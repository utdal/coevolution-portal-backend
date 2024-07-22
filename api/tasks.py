from celery import shared_task
import time
from typing import Union, TextIO, Literal
import tempfile

@shared_task
def get_msa_task(seq):
    time.sleep(10)
    return seq + "\nabc\ndef\nAdditional sequences..."

@shared_task
def get_DI_pairs_task(seq):
    time.sleep(15)
    return [(1, 2), (3, 4), (5, 6)]

@shared_task
def hmmsearch_from_seed(seed_sequence: Union[str, TextIO], protein_name: str, max_gaps: int=10000):
    # If a real HMM profile is found, seed sequence is ignored. Otherwise, it is required.

    # Supply a name for your HMM profile, regardless of whether you're building it or have one in your file system.
    hmm_prof_fname = f"{protein_name}_HMM"
    # Supply a name for your seed sequence. This is optional if you wish to search with an already produced profile HMM.
    #seed_seq_fname = f"{protein_name}.fasta"
	
    if type(seed_sequence) == str:    
        tmp = tempfile.TemporaryFile()
        # Open the file for writing.
        with open(tmp.name, 'w') as f:
            f.write(seed_sequence)

    # Define a database path for hmmsearch to search through.
    database_path = "/mfs/io/groups/morcos/uniprot_db/uniprot_sprot_trembl.fasta"

    # File extensions are added for you. Just put a basename for your output MSAs.
    MSA_fname = f"{protein_name}_MSA"

    # Remove intermediate .sto and .afa files. This leaves only the fasta file (named __.afa_filtered_____)
    remove_intermediates=True

    # Check to see if max_gaps is a valid number >= 0.
    if max_gaps.isnumeric():
        max_gaps = int(max_gaps)

	/mfs/io/groups/morcos/g1petastore_transfer/share/hmmer/bin/hmmbuild $hmm_prof_fname $seed_seq_fname > /dev/null 2>&1
	
    #	The profile exists. We can now do hmmsearch.

	/mfs/io/groups/morcos/g1petastore_transfer/share/hmmer/bin/hmmsearch -A $sto_name $hmm_prof_fname $database > /dev/null 2>&1
	
    # Convert to afa format
	/mfs/io/groups/morcos/g1petastore_transfer/share/hmmer/bin/esl-reformat -o $afa_name afa $sto_name

	/mfs/io/groups/morcos/g1petastore_transfer/share/hmmer/filter_pfam_args_updated.py $afa_name $max_gaps
	