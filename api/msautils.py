from typing import Optional, Union
from numpy import percentile
import numpy.typing as npt
import io
import os
import re
from dcatoolkit import DirectInformationData, ResidueAlignment, StructureInformation
from dcatoolkit import MSATools
from pyhmmer.plan7 import Background, HMM, Profile, OptimizedProfile, HMMFile, Pipeline, Builder
from pyhmmer.easel import MSA, TextMSA, MSAFile, Alphabet, TextSequence, SequenceFile
from pyhmmer.hmmer import hmmalign, hmmscan

def generate_hmm_and_profiles(seed_sequence_filepath: str, seed_name: str) -> tuple[Background, HMM, Profile, OptimizedProfile]:
    """
    Generate the background, the HMM, the HMM Profile, and a Pyhmmer Optimized HMM Profile from the seed sequence and name supplied.

    Parameters
    ----------
    seed_sequence_filepath : str
        Filepath of the seed sequence used to generate the HMM.
    seed_name : str
        The name of the seed supplied. Used to label the seed sequence in its aligned format.

    Returns
    -------
    tuple[pyhmmer.plan7.Background, pyhmmer.plan7.HMM, pyhmmer.plan7.Profile, pyhmmer.plan7.OptimizedProfile]
        Background, HMM, Profile, and OptimizedProfile. The background is characterized by the amino acid alphabet. The HMM and Profiles are built from pyhmmer.plan7.Builder.build_msa()
    """
    aa_alphabet = Alphabet.amino()
    seed_MSA_fname = seed_sequence_filepath
    
    with MSAFile(seed_MSA_fname, digital=False, alphabet=aa_alphabet) as msa_fs:
        loaded_seed = msa_fs.read()
        if isinstance(loaded_seed, TextMSA):
            loaded_seed_text: TextMSA = loaded_seed
        else:
            raise TypeError("The seed sequence(s) provided are not in the format of a text MSA")
        # Must convert to a digital MSA according to https://pyhmmer.readthedocs.io/en/stable/examples/msa_to_hmm.html
        loaded_seed_digital = loaded_seed_text.digitize(alphabet=aa_alphabet)
        builder = Builder(alphabet=aa_alphabet)
        background = Background(alphabet=aa_alphabet)
        loaded_seed_digital.name = f"{seed_name}_MSA".encode()
        hmm, profile, optimized_profile = builder.build_msa(loaded_seed_digital, background)
        return background, hmm, profile, optimized_profile
    raise ValueError("Invalid hmm data produced.")


def hmmsearch_from_seed(seed_sequence_filepath: str, seed_name: str, E: Optional[float], T: Optional[float] = None, database_path: str="/mfs/io/groups/morcos/uniprot_db/uniprot_sprot_trembl.fasta") -> TextMSA:
    """
    Generates an HMM and associated files needed and produces an MSA using hmmsearch functionality.

    Parameters
    ----------
    seed_sequence_filepath : str
        Filepath of the seed sequence used to generate the HMM.
    seed_name : str
        The name of the seed supplied. Used to label the seed sequence in its aligned format.
    T : float, optional
        The bit score value target sequences must meet. See hmmsearch from Eddy's lab and search_hmm from pyhmmer.
    database_path:
        Filepath of the full sequence database that the profile produced is searched against.
    
    Returns
    -------
    pyhmmer.easel.TextMSA
        TextMSA representation of hits found via hmmsearch of HMM against the sequence database specified.
    """
    aa_alphabet = Alphabet.amino()
    background, hmm, _, _ = generate_hmm_and_profiles(seed_sequence_filepath, seed_name)
    if E:
        pipeline = Pipeline(alphabet=aa_alphabet, background=background, E=E)
    elif T:
        pipeline = Pipeline(alphabet=aa_alphabet, background=background, T=T)
    else:
        pipeline = Pipeline(alphabet=aa_alphabet, background=background)
    hits = None
    with SequenceFile(database_path, digital=True, alphabet=aa_alphabet) as seq_file:
        hits = pipeline.search_hmm(hmm, seq_file)
    if hits:
        produced_msa: MSA = hits.to_msa(alphabet=aa_alphabet, digitize=False)
        if isinstance(produced_msa, TextMSA):
            return produced_msa
        else:
            raise TypeError("The produced MSA is not an MSA in text format.")
    else:
        raise ValueError("No hits found.")


def produce_alignment_to_protein(seed_name: str, seed_sequence_filepath: str, protein_name: str, protein_sequence: str, valid_residues: list[tuple[int, str]]) -> ResidueAlignment:
    """
    Produces a ResidueAlignment object that represents the alignment between the MSA generated from an HMM and a specified target protein sequence.

    Parameters
    ----------
    protein_sequence : str
        Sequence of protein to align pairs to.
    seed_sequence_filepath : str
        Filepath of the seed sequence used to generate the HMM & Profiles needed to produce the MSA.
    seed_name : str
        The name of the seed supplied. Used to label the domain portion of the alignment.
    protein_name : str
        The name of the protein supplied. Used to label the target portion of the alignment.

    Returns
    -------
    dcatoolkit.analytics.ResidueAlignment
        ResidueAlignment object generated from input of parameters returned from hmmscan with the same HMM used to produce the MSA and the target's protein sequence.
    """
    aa_alphabet = Alphabet.amino()
    background, hmm, profile, optimized_profile = generate_hmm_and_profiles(seed_sequence_filepath, seed_name)
    protein_query = TextSequence(name=f"{protein_name}".encode(), sequence=protein_sequence).digitize(alphabet=aa_alphabet)
    hits = list(hmmscan(queries=protein_query, profiles=[hmm], background=background))
    # Queries refers to the protein sequence, which yields the target of the alignment.
    # Profiles refers to the domain's profile HMM generated from the domain / full protein's seed sequence. The same HMM used to generate an MSA.
    best_alignment = hits[0][0].best_domain.alignment
    
    return ResidueAlignment(best_alignment.hmm_name.decode(), best_alignment.target_name.decode(), best_alignment.hmm_from, best_alignment.target_from, best_alignment.hmm_sequence, best_alignment.target_sequence, valid_residues=valid_residues)


def align_sequences_with_hmm(sequences: Union[list[str], str, io.IOBase], 
                             hmm: Union[str, io.BytesIO], 
                             headers: Optional[Union[str, list[str]]] = None) -> dict:
    """

    Sequences are aligned to profile hmm. Sequences may be formatted in multiple ways, but if
    provided as str or list of strings, headers may be provided. If sequences are provided as a fasta,
    headers from the file are used.

    Parameters
    ----------
    sequences - can be string, list of strings, or fasta file
    hmm - can be file path/name or file object
    headers - Optional: can be string or list of strings describing the sequences provided. Only used if
              sequences are provided as a string or list of strings. Otherwise, the headers from the fasta 
              are used

    Returns
    -------
    Dictionary where keys are headers and values are aligned sequences.

    """
    parsed_sequences = None

    with HMMFile(hmm) as hmm_file:
        hmm = hmm_file.read()
    
    if not isinstance(sequences, list):
        # Check to see if FASTA
        if isinstance(sequences, str):
            sequences = sequences.split()
        elif isinstance(sequences, io.StringIO):
            sequences = sequences.getvalue().split()
        else:
            headers_from_MSA, sequences_from_MSA = zip(*MSATools.load_from_file(sequences).MSA)
            headers = list(headers_from_MSA)
            sequences = list(sequences_from_MSA)

    if isinstance(sequences, list) and len(sequences) > 0:
        parsed_sequences = []
        for count, sequence in enumerate(sequences):
            if headers:
                parsed_sequences.append(TextSequence(name=headers.pop(0).encode(), sequence=sequence).digitize(Alphabet.amino()))
            else:
                parsed_sequences.append(TextSequence(name=f"Sequence {str(count+1)}".encode(), sequence=sequence).digitize(Alphabet.amino()))    
        
    if hmm is not None and parsed_sequences is not None:
        aligned_sequences = hmmalign(hmm, parsed_sequences, trim=True)

        if isinstance(aligned_sequences, TextMSA):
            return format_aligned_seqs(aligned_sequences)
        else:
            raise ValueError("Aligned sequences are not a TextMSA")
    else:
        raise ValueError("HMM, Original MSA, or sequences not loaded correctly or missing.")


def format_aligned_seqs(aligned_obj):
    """

    Formats aligned sequence object into a dictionary where keys are the headers and sequences
    are the values. If the sequence has been aligned, all . and lower chars are removed

    Parameters
    ----------
    aligned_obj - pyhmmer.easel.TextMSA object 

    Returns
    -------
    Dictionary where keys are headers and values are aligned sequences.

    """
    formatted = {}
    for idx, item in enumerate(aligned_obj.names):
        seq = re.sub(r"[a-z].", "", aligned_obj.alignment[idx])
        formatted[item.decode().replace(">","")] = seq
    return formatted


def combine_easel_TextMSA(text_msa1: TextMSA, text_msa2: TextMSA):
    
    all_sequence_names: list[bytes] = []
    all_sequence_alignments = []
    for text_sequence in text_msa1.sequences:
        all_sequence_names.append(text_sequence.name)
    for text_sequence in text_msa2.sequences:
        all_sequence_names.append(text_sequence.name)
    all_sequence_alignments = text_msa1.alignment + text_msa2.alignment

    for name, sequence in zip(all_sequence_names, all_sequence_alignments):
        print(f">{name.decode()}")
        print(sequence)


def get_mapped_residues(DI_arr: npt.NDArray, seed_name: str, seed_sequence_filepath: str, protein_name: str, protein_sequence_1: str, protein_sequence_2: str, valid_residues_1: list[tuple[int, str]], valid_residues_2: list[tuple[int, str]], pairs_only: bool=False) -> npt.NDArray:
    """
    Get the residues supplied mapped to the protein structure indexed at the RCSB PDB id supplied. The elements of pairs are mapped to chain1 and chain2 supplied respectively.

    Parameters
    ----------
    DI_arr : numpy.ndarray
        Array of DI pairs and their values represented as a 3-column ndarray.
    rcsb_pdb_id : str
        The PDB ID of the protein structure of interest that will be fetched from RCSB.
    seed_name : str
        The name of the seed supplied. Used to label the domain portion of the alignment.
    seed_sequence_filepath : str
        Filepath of the seed sequence used to generate the HMM & Profiles needed to produce the MSA.
    protein_name : str
        The name of the protein supplied. Used to label the target portion of the alignment.
    protein_sequence_1 : str
        Sequence of the protein or chain that the first column of your DI array maps to.
    protein_sequence_2 : str
        Sequence of the protein or chain that the second column of your DI array maps to.
    protein_offset_1 : int
        Residue index where the first protein sequence starts.
    protein_offset_2 : int
        Residue index where the second protein sequence starts.
    pairs_only : bool
        True if we should drop the 3rd, DI, column.
    
    
    Returns
    -------
    mapped_residues : numpy.ndarray
        The residues corresponding to the MSA generated from the HMM profile mapped to the structure supplied.
    """
    res_align_1 = produce_alignment_to_protein(protein_sequence=protein_sequence_1, seed_sequence_filepath=seed_sequence_filepath, seed_name=seed_name, protein_name=protein_name, valid_residues=valid_residues_1)
    res_align_2 = produce_alignment_to_protein(protein_sequence=protein_sequence_2, seed_sequence_filepath=seed_sequence_filepath, seed_name=seed_name, protein_name=protein_name, valid_residues=valid_residues_2)
    DI_data = DirectInformationData.load_as_ndarray(DI_arr)
    mapped_residues = DI_data.get_ranked_mapped_pairs(res_align_1, res_align_2, pairs_only=pairs_only)
    #print(mapped_residues)
    print(res_align_1)
    return mapped_residues


def filter_by_consecutive_gaps(input_source: Union[str, io.IOBase], output_source: Union[str, io.IOBase], perc_max_gaps: Optional[int]) -> None:
    """
    Filters specified input source by the number of maximum continuous gaps supplied and writes to output source.

    Parameters
    ----------
    input_source : str or io.IOBase
        Filepath (if str) where the MSA to be filtered is located. If the input source is a IOBase object, then it will be considered the MSA.
    output_source : str or io.IOBase
        Output filepath to write the filtered MSA to. If the output source is an IOBase object, then the MSA will be written to the IOBase object.
    max_gaps : int, optional
        Number of maximum continuous gaps that the final MSA should be allowed to have. If set to None, it will not filter based off of any maximum number of continuous gaps, but will clean the afa.
        
    Returns
    -------
    None
    """
    input_MSA = MSATools.load_from_file(input_source)
    input_MSA_cols = len(input_MSA.MSA[0][1])
    if perc_max_gaps:
        max_gaps = int((perc_max_gaps / 100) * input_MSA_cols)
    else:
        max_gaps = None
    output_MSA = MSATools(input_MSA.filter_by_continuous_gaps(max_gaps))
    output_MSA.write(output_source)

    
def get_msa_stats(msa_path: str) -> tuple[int, int]:
    """
    Get the number of rows and columns from an MSA loaded from the supplied MSA filepath.

    Parameters
    ----------
    msa_path:
        Filepath of Multiple Sequence Alignment.

    Returns
    -------
    rows, cols : tuple[int, int]
        Number of rows and number of columns in the MSA.
    """
    msa = MSATools.load_from_file(msa_path)
    rows = len(msa)
    cols = len(msa.MSA[0][1])
    return rows, cols


from dca.dca_class import dca
import numpy as np
import matplotlib.pyplot as plt

def run_dca_internal(filepath: str):
    protein_family = dca(filepath)
    protein_family.mean_field()
    np.savetxt(f"{filepath.split("_")[0]}.DI", protein_family.DI)

def plot_dca_internal(pdb_id, pdb_type, chain, auth_chain, auth_seq_id, seed_name):
    DI_arr = np.loadtxt(f'{pdb_id}/{pdb_id}_mat.DI')[:, [0,1,3]]
    DI_arr = DI_arr[DI_arr[:,2].argsort()[::-1]]
    DI_arr = DI_arr[:800]
    
    coords = []
    if pdb_type == 'mmcif':
        struc = StructureInformation.fetch_pdb(pdb_id, pdb_type)
        coords = struc.get_contacts(False, 8, chain, chain, auth_seq_id=auth_seq_id, auth_chain_id_supplied=auth_chain)
        chain_seq = struc.get_non_missing_sequence(chain, auth_chain)
        DI_arr = get_mapped_residues(DI_arr, seed_name, f'{pdb_id}/{pdb_id}_seed.fasta', pdb_id, chain_seq, chain_seq, struc.get_valid_chain_residues(chain_id=chain, auth_seq_id=auth_seq_id, auth_chain_id_supplied=auth_chain), struc.get_valid_chain_residues(chain_id=chain, auth_seq_id=auth_seq_id, auth_chain_id_supplied=auth_chain))
    elif pdb_type == 'pdb':
        struc = StructureInformation.fetch_pdb(pdb_id, pdb_type)
        coords = struc.get_contacts(False, 8, chain, chain)
        chain_seq = struc.get_non_missing_sequence(chain)
        DI_arr = get_mapped_residues(DI_arr, seed_name, f'{pdb_id}/{pdb_id}_seed.fasta', pdb_id, chain_seq, chain_seq, struc.get_valid_chain_residues(chain_id=chain), struc.get_valid_chain_residues(chain_id=chain))

        
    DI_arr = np.array(DI_arr.tolist())
    #print(DI_arr)
    plt.scatter([x for x,y in coords], [y for x, y in coords], s=3, c='grey')
    plt.scatter(DI_arr[:, 0], DI_arr[:, 1], s=2, c='red')
    plt.show()

glitchy_msas = ['1pzs/1pzs_MSA.afa_filtered10000_filtered48', '3d7i/3d7i_MSA.afa_filtered10000_filtered21', '3ddv/3ddv_MSA.afa_filtered10000_filtered47', '3f52/3f52_MSA.afa_filtered10000_filtered22']
#for glitchy_msa in glitchy_msas:
# run_dca_internal(glitchy_msas[3 ])


#print(produce_alignment_to_protein('CISD3_seed_truc', 'CISD3_seed_truc.fasta', '6avj', StructureInformation.fetch_pdb("6avj", 'pdb').get_non_missing_sequence('A'), 0))
#print(produce_alignment_to_protein("1pzs_seed", "1pzs_seed.fasta", "1pzs_protein", struc_1pzs.non_missing_sequences['A'], struc_1pzs.get_shift_values('A', 'A')[0]))

# struc_3d7i = StructureInformation.fetch_pdb("3d7i", 'pdb')
# print(type(struc_3d7i))
# print(list(sorted(struc_3d7i.get_contacts(False, 8, 'A', 'A', True))))
# print(struc_3d7i.get_shift_values('A', 'A'))

#struc_1pzs_cif = StructureInformation.fetch_pdb("1pzs", 'mmcif')
#struc_1pzs_pdb = StructureInformation.fetch_pdb("1pzs", 'pdb')

#print(struc_1pzs_cif.get_shift_values('A', 'A', False))     # Apply the shift iff the auth_res_ids is TRUE. The author is the one that's shifted, not my 1-indexed CIF
#print(struc_1pzs_pdb.get_shift_values('A', 'A'))            # Apply the shift iff the auth_res_ids is 

#plot_dca_internal('3ddv', 'mmcif', 'B', False, False, 'decarboxylase')

#print(struc_1pzs_cif.get_non_missing_sequence('A'))
#print(StructureInformation.fetch_pdb("6avj", 'mmcif').get_valid_chain_residues('A'))
#print(produce_alignment_to_protein('SODS', '1pzs/1pzs_seed copy.fasta', '1pzs', "QSLTSTLTAPDGTKVATAKFEFANGYATVTIATTGVGKLTPGFHGLHIHQVGKCEPNSVAPTGGAPGNFLSAGGHYHVPGHTGTPASGDLASLQVRGDGSAMLVTTTDAFTMDDLLSGAKTAIIIHAGADNFANIPPERYVQVNGTPGPDETTLTTGDAGKRVACGVIGSG", 0))
plot_dca_internal('3ddv', 'mmcif', 'B', False, False, 'decarboxylase')