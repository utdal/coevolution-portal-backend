from django.conf import settings
from django.utils import timezone
from django.core.files import File
from celery import shared_task
import time
from typing import Union, TextIO
import tempfile
import pyhmmer
from dca import dca_class

from .models import APITaskMeta, CeleryTaskMeta, APIDataObject, MultipleSequenceAlignment, DirectCouplingAnalysis
from .taskutils import APITaskBase


@shared_task(base=APITaskBase, bind=True)
def generate_msa_task(self, seed, msa_name=None):
    self.set_progress(message="Getting ready", percent=0)
    time.sleep(10)
    self.set_progress(message="Working on it", percent=30)
    time.sleep(10)
    self.set_progress(message="Taking a break", percent=60)
    time.sleep(20)
    self.set_progress(message="Getting back to it", percent=90)
    time.sleep(10)

    with tempfile.TemporaryFile("a+") as f:
        f.write(
            f">Dummy MSA\n{seed}\n>Sequence2\n{seed}\n>Sequence3\n{seed[::-1]}"
        )

        msa = MultipleSequenceAlignment.objects.create(
            id=self.get_task_id(),
            user=self.get_user(),
            expires=timezone.now() + settings.DATA_EXPIRATION,
        )
        if msa_name is None:
            msa_name = self.get_task_id()
        
        msa.fasta = File(f, msa_name)
        msa.quality = MultipleSequenceAlignment.Qualities.GOOD
        msa.depth = 3
        msa.cols = len(seed)
        msa.save()
    
    self.set_progress(message="Finally done!", percent=90)


@shared_task(base=APITaskBase, bind=True)
def compute_dca_task(self, msa_id):
    prev_task = CeleryTaskMeta.objects.filter(id=msa_id)
    if prev_task.exists():
        self.set_progress(message="Waiting for MSA", percent=0)
        prev_task.first().wait_for_completion()
    
    msa = MultipleSequenceAlignment.objects.get(id=msa_id)

    self.set_progress(message="Running DCA", percent=10)
    protein_family = dca_class.dca(msa.fasta.path)
    protein_family.mean_field()

    dca = DirectCouplingAnalysis.objects.create(
        id=self.get_task_id(),
        user=self.get_user(),
        expires=timezone.now() + settings.DATA_EXPIRATION,
    )
    dca.e_ij = protein_family.couplings
    dca.h_i = protein_family.localfields
    dca.m_eff = protein_family.Meff
    dca.ranked_di = protein_family.DI
    dca.save()
    self.set_progress(message="", percent=100)


@shared_task
def cleanup_expired_data():
    old_tasks = APITaskMeta.objects.filter(expires__lte=timezone.now())
    old_data = APIDataObject.objects.filter(expires__lte=timezone.now())
    
    if len(old_tasks) or len(old_data):
        print(f"{len(old_tasks)} tasks and {len(old_data)} objects have expired.")

        if settings.DELETE_EXPIRED_DATA:
            print("Deleting...")
            old_tasks.delete()
            old_data.delete()
