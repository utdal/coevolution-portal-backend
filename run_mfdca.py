from dca.dca_class import dca
import numpy as np
protein_family = dca('1pzs_MSA.afa_filtered10000_filtered48')
protein_family.mean_field()
np.savetxt("1pzs.DI", protein_family.DI)