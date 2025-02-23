import numpy as np

aa2num = {
        '-': 0,
        'A': 1,    
        'C': 2,
        'D': 3,
        'E': 4,
        'F': 5,
        'G': 6,
        'H': 7,
        'I': 8,
        'K': 9,
        'L': 10,
        'M': 11,
        'N': 12,
        'P': 13,
        'Q': 14,
        'R': 15,
        'S': 16,
        'T': 17,
        'V': 18,
        'W': 19,
        'Y': 20
}


def calc_Hamiltonian(seq_list, coupling_tbl, lf_tbl):
    H = np.zeros(len(seq_list))
    
    for seq_idx, seq in enumerate(seq_list):
        nums = np.array([aa2num[aa] for aa in seq])
        
        # Add all local fields at once using numpy operations
        H[seq_idx] += np.sum([lf_tbl.iloc[num, pos] for pos, num in enumerate(nums)])
        
        # Compute all coupling pairs at once
        positions = np.arange(len(nums))
        i_indices = [21 * pos + nums[pos] for pos in positions]
        
        # Create all pairs of positions efficiently
        pairs = [(i, j) for i in range(len(nums)) for j in range(i + 1, len(nums))]
        j_indices = [21 * pair[1] + nums[pair[1]] for pair in pairs]
        i_indices_pairs = [21 * pair[0] + nums[pair[0]] for pair in pairs]
        
        # Sum all coupling terms at once
        H[seq_idx] += np.sum([coupling_tbl.iloc[i, j] for i, j in zip(i_indices_pairs, j_indices)])
    
    return -H

