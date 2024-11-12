from django.conf import settings
from django.utils import timezone
from django.core.files import File
from django.core.files.base import ContentFile
from celery import shared_task
import time
from typing import Union, TextIO
import tempfile
from dca import dca_class
import numpy as np
import json
import os
import io

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
def generate_msa_task(self, seed, msa_name=None, E=None, perc_max_gaps=None):
    self.set_progress(message="Starting...", percent=0)
    if msa_name is None:
        msa_name = self.get_task_id()

    seed = seed.replace("\n", "")

    f = ContentFile(f">{msa_name}\n{seed}", name=msa_name)
    seedObj = SeedSequence.objects.create(
        name=msa_name, fasta=f
    )

    self.set_progress(message="Doing HMM search...", percent=10)

    preprocessed_msa = hmmsearch_from_seed(seedObj.fasta.path, msa_name, database_path=settings.HMM_DATABASE, E=E)

    self.set_progress(message="Filtering!", percent=90)

    msa = MultipleSequenceAlignment.objects.create(
        id=self.get_task_id(),
        user=self.get_user(),
        expires=timezone.now() + settings.DATA_EXPIRATION,
        seed=seedObj,
        fasta=ContentFile("", msa_name)
    )

    preprocessed_file = io.BytesIO()
    preprocessed_msa.write(preprocessed_file, "afa")
    filter_by_consecutive_gaps(preprocessed_file, msa.fasta.path, perc_max_gaps)

    msa.quality = MultipleSequenceAlignment.Qualities.GOOD
    rows, cols = get_msa_stats(msa.fasta.path)
    msa.depth = rows
    msa.cols = cols
    msa.save()

    self.set_progress(message="", percent=100)


@shared_task(base=APITaskBase, bind=True)
def compute_dca_task(self, msa_id, theta = 0.2, wait=True):
    prev_task = CeleryTaskMeta.objects.filter(id=msa_id)
    if prev_task.exists() and wait:
        self.set_progress(message="Waiting for MSA", percent=0)
        prev_task.first().wait_for_completion()

    msa = MultipleSequenceAlignment.objects.get(id=msa_id)

    self.set_progress(message="Running DCA", percent=10)
    protein_family = dca_class.dca(msa.fasta.path)
    protein_family.mean_field(theta=theta)

    dca = DirectCouplingAnalysis.objects.create(
        id=self.get_task_id(),
        user=self.get_user(),
        expires=timezone.now() + settings.DATA_EXPIRATION,
        msa=msa
    )

    # Limit to top 5000
    di = protein_family.DI
    di = di[di[:, 2].argsort()[::-1]]
    di = di[:5000]

    # Not currently used, takes a lot of space
    # dca.e_ij = protein_family.couplings
    # dca.h_i = protein_family.localfields
    dca.m_eff = protein_family.Meff
    dca.ranked_di = di
    dca.save()
    self.set_progress(message="", percent=100)


@shared_task(base=APITaskBase, bind=True)
def map_residues_task(self, dca_id, pdb_id, chain1, chain2, auth_chain_id_supplied, wait=True):
    prev_task = CeleryTaskMeta.objects.filter(id=dca_id)
    if prev_task.exists() and wait:
        self.set_progress(message="Waiting for MSA", percent=0)
        prev_task.first().wait_for_completion()

    dca = DirectCouplingAnalysis.objects.get(id=dca_id)
    # assert dca.msa and dca.msa.seed, "The DCA must have a seed"
    if dca.msa.seed:
        seed = dca.msa.seed
    else:
        seed = SeedSequence.objects.create(
            name="Not a great seed name",
            fasta=dca.msa.fasta
        )
    
    self.set_progress(message="Mapping residues", percent=10)
    # StructureInformation.fetch_pdb(pdb_id) # Called in get_mapped_residues
    mapped_di = get_mapped_residues(
        dca.ranked_di, pdb_id, seed.fasta.path, seed.name, pdb_id, chain1, chain2, auth_chain_id_supplied=auth_chain_id_supplied
    )

    MappedDi.objects.create(
        id=self.get_task_id(),
        protein_name=pdb_id,
        seed=seed,
        dca=dca,
        mapped_di=mapped_di,
    )
    self.set_progress(message="", percent=100)


@shared_task(base=APITaskBase, bind=True)
def generate_contacts_task(
    self, pdb_id: str, ca_only: bool = False, threshold: float = 8, is_cif: bool = True
):
    self.set_progress(message="Generating contacts", percent=0)

    contacts_dict = {}
    if is_cif:
        structure_info = StructureInformation.fetch_pdb(pdb_id)
        for chain_id_1 in structure_info.unique_chains:
            for chain_id_2 in structure_info.unique_chains:
                contacts_name = f"{chain_id_1} [auth {structure_info.chain_auth_dict[chain_id_1]}], {chain_id_2} [auth {structure_info.chain_auth_dict[chain_id_2]}]"
                contacts = structure_info.get_contacts(
                    ca_only, threshold, chain_id_1, chain_id_2
                )
                contacts = [(int(a), int(b)) for a, b in contacts] # sets and np ints not JSON serializable
                contacts_dict[contacts_name] = contacts
    else:
        structure_info = StructureInformation.fetch_pdb(pdb_id, 'pdb')
        for chain_id_1 in structure_info.unique_chains:
            for chain_id_2 in structure_info.unique_chains:
                contacts_name = f"{chain_id_1}, {chain_id_2}"
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
