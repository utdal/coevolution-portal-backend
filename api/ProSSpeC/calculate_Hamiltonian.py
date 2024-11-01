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
        nums = [aa2num[aa] for aa in seq]

        # Add local fields
        H[seq_idx] += sum([lf_tbl.iloc[num,num_idx] for num_idx, num in enumerate(nums)]) 

        # Add couplings
        for num_idx in range(0, len(nums)):
            i = 21*(num_idx)+nums[num_idx]
            for pair in range(num_idx+1,len(nums)):
                j = 21*(pair)+nums[pair]
                H[seq_idx] += coupling_tbl.iloc[i,j]
    return -H

