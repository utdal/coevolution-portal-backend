from celery import Celery
import dcautils

celery = Celery('worker', broker='redis://localhost:6379', backend='redis://localhost:6379')

@celery.task
def generate_msa_task(seq):
    return dcautils.generate_msa(seq)

@celery.task
def get_DI_pairs_task(seq):
    return dcautils.get_DI_pairs(seq)