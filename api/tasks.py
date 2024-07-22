from celery import shared_task
import time
from dca.dca_class import dca
import os

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