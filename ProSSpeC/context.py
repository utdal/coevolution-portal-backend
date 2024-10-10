import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from msautils import align_sequences_with_hmm, combine_easel_TextMSA