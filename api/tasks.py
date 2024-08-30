from django.conf import settings
from django.utils import timezone
from django.core.files import File
from celery import shared_task
import time
from typing import Union, TextIO
import tempfile
from dca import dca_class
import numpy as np
import json
import os

from .models import (
    APITaskMeta,
    CeleryTaskMeta,
    APIDataObject,
    MultipleSequenceAlignment,
    DirectCouplingAnalysis,
    SeedSequence,
    MappedDi,
    StructureContacts,
)
from .taskutils import APITaskBase
from .msautils import (
    hmmsearch_from_seed,
    filter_by_consecutive_gaps,
    get_mapped_residues,
    get_msa_stats,
)
from dcatoolkit import StructureInformation


@shared_task(base=APITaskBase, bind=True)
def generate_msa_task(self, seed, msa_name=None, max_gaps=None):
    if msa_name is None:
        msa_name = self.get_task_id()

    seed = seed.replace("\n", "")

    with tempfile.TemporaryFile("a+") as f:
        f.write(f">{msa_name}\n{seed}")

        seedObj = SeedSequence.objects.create(
            id=self.get_task_id(), name=msa_name, fasta=File(f, msa_name)
        )

    self.set_progress(message="Doing HMM search...", percent=10)

    preprocessed_msa = hmmsearch_from_seed(seedObj.fasta.name, msa_name)

    preprocessed_file = tempfile.NamedTemporaryFile(delete=False)
    try:
        with open(preprocessed_file.name, "wb") as fs:
            preprocessed_msa.write(fs, "afa")

        msa = MultipleSequenceAlignment.objects.create(
            id=self.get_task_id(),
            user=self.get_user(),
            expires=timezone.now() + settings.DATA_EXPIRATION,
        )

        self.set_progress(message="Filtering!", percent=90)

        filter_by_consecutive_gaps(preprocessed_file.name, msa.fasta.path, max_gaps)

        msa.quality = MultipleSequenceAlignment.Qualities.GOOD
        rows, cols = get_msa_stats(msa.fasta.path)
        msa.depth = rows
        msa.cols = cols
        msa.save()

    finally:
        os.remove(preprocessed_file.name)

    self.set_progress(message="", percent=100)


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


@shared_task(base=APITaskBase, bind=True)
def map_residues_task(self, dca_id, pdb_id, seed_id, chain1, chain2):
    dca = DirectCouplingAnalysis.objects.get(id=dca_id)
    seed = SeedSequence.objects.get(id=seed_id)
    StructureInformation.fetch_pdb(pdb_id)
    mapped_di = get_mapped_residues(
        dca.ranked_di, pdb_id, seed.fasta.path, seed.name, pdb_id, chain1, chain2
    )

    MappedDi.objects.create(
        id=self.get_task_id(),
        protein_name=pdb_id,
        seed=seed,
        dca=dca,
        mapped_di=mapped_di,
    )


@shared_task(base=APITaskBase, bind=True)
def generate_contacts_task(
    self, pdb_id: str, ca_only: bool = False, threshold: float = 8
):
    structure_info = StructureInformation.fetch_pdb(pdb_id)
    contacts_dict = {}
    for chain_id_1 in structure_info.unique_chains:
        for chain_id_2 in structure_info.unique_chains:
            contacts_name = str(chain_id_1) + str(chain_id_2) + "_contacts"
            contacts = structure_info.get_contacts(
                ca_only, threshold, chain_id_1, chain_id_2
            )
            contacts = [(int(a), int(b)) for a, b in contacts] # sets and np ints not JSON serializable
            contacts_dict[contacts_name] = contacts
    StructureContacts.objects.create(
        id=self.get_task_id(),
        pdb_id=pdb_id,
        ca_only=ca_only,
        threshold=threshold,
        contacts=contacts_dict,
    )


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
