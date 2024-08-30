from typing import Optional
import numpy.typing as npt

from dcatoolkit import DirectInformationData, ResidueAlignment, StructureInformation
from dcatoolkit import MSATools
import pyhmmer


#alphabet used in production of MSAs and HMMs.
def generate_hmm_and_profiles(seed_sequence_filepath: str, seed_name: str) -> tuple:
    aa_alphabet = pyhmmer.easel.Alphabet.amino()
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

def hmmsearch_from_seed(seed_sequence_filepath: str, seed_name: str, database_path: str="/mfs/io/groups/morcos/uniprot_db/uniprot_sprot_trembl.fasta"):
    aa_alphabet = pyhmmer.easel.Alphabet.amino()
    background, hmm, _, _ = generate_hmm_and_profiles(seed_sequence_filepath, seed_name)
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

def filter_by_consecutive_gaps(input_filepath: str, output_filepath: str, max_gaps: Optional[int]):
    input_MSA = MSATools.load_from_file(input_filepath)
    output_MSA = MSATools(input_MSA.filter_by_continuous_gaps(max_gaps))
    output_MSA.write(output_filepath)

def produce_alignment_to_protein(protein_sequence: str, seed_sequence_filepath: str, seed_name: str, protein_name: str):
    aa_alphabet = pyhmmer.easel.Alphabet.amino()
    background, hmm, profile, optimized_profile = generate_hmm_and_profiles(seed_sequence_filepath, seed_name)
    protein_query = pyhmmer.easel.TextSequence(name=f"{protein_name}".encode(), sequence=protein_sequence).digitize(alphabet=aa_alphabet)
    hits = list(pyhmmer.hmmer.hmmscan(queries=protein_query, profiles=[hmm], background=background))
    # Queries refers to the protein sequence, which yields the target of the alignment.
    # Profiles refers to the domain's profile HMM generated from the domain / full protein's seed sequence. The same HMM used to generate an MSA.
    best_alignment = hits[0][0].best_domain.alignment
    return ResidueAlignment(best_alignment.hmm_name.decode(), best_alignment.target_name.decode(), best_alignment.hmm_from, best_alignment.target_from, best_alignment.hmm_sequence, best_alignment.target_sequence)

def get_mapped_residues(DI_arr: npt.NDArray, rcsb_pdb_id: str, seed_sequence_filepath, seed_name, protein_name, chain1, chain2):
    structure = StructureInformation.fetch_pdb(rcsb_pdb_id)
    res_align = produce_alignment_to_protein(structure.get_non_missing_sequence(chain1), seed_sequence_filepath=seed_sequence_filepath, seed_name=seed_name, protein_name=protein_name)
    res_align = produce_alignment_to_protein(structure.get_non_missing_sequence(chain2), seed_sequence_filepath=seed_sequence_filepath, seed_name=seed_name, protein_name=protein_name)
    DI_data = DirectInformationData.load_as_ndarray(DI_arr)
    mapped_residues = DI_data.get_ranked_mapped_pairs(res_align, res_align, pairs_only=False)
    return mapped_residues

def get_msa_stats(msa_path: str):
    msa = MSATools.load_from_file(msa_path)
    rows = len(msa)
    cols = len(msa.MSA[0][1])
    return rows, cols