from celery import shared_task
import time

@shared_task
def get_msa_task(seq):
    time.sleep(10)
    return seq + "\nabc\ndef\nAdditional sequences..."

@shared_task
def get_DI_pairs_task(seq):
    time.sleep(15)
    return [(1, 2), (3, 4), (5, 6)]