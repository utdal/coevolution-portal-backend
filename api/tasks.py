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
def hmmsearch_from_seed(
    seed_sequence: Union[str, TextIO], protein_name: str, max_gaps: int = 10000
):
    # alphabet used in production of MSAs and HMMs.
    aa_alphabet = pyhmmer.easel.Alphabet.amino()
    # If a real HMM profile is found, seed sequence is ignored. Otherwise, it is required.

    # Supply a name for your HMM profile, regardless of whether you're building it or have one in your file system.
    hmm_prof_fname = f"{protein_name}_HMM"
    # Supply a name for your seed sequence. This is optional if you wish to search with an already produced profile HMM.
    # seed_seq_fname = f"{protein_name}.fasta"

    if type(seed_sequence) == str:
        tmp = tempfile.NamedTemporaryFile()
        # Open the file for writing.
        tmp.name = ""
        with open(tmp.name, "w") as f:
            f.write(seed_sequence)
        MSA_fname = tmp.name
    else:
        MSA_fname = seed_sequence

    # Define a database path for hmmsearch to search through.
    database_path = "/mfs/io/groups/morcos/uniprot_db/uniprot_sprot_trembl.fasta"

    # Remove intermediate .sto and .afa files.
    remove_intermediates = True

    # Check to see if max_gaps is a valid number >= 0.
    if max_gaps.isnumeric():
        max_gaps = int(max_gaps)

        # /mfs/io/groups/morcos/g1petastore_transfer/share/hmmer/bin/hmmbuild $hmm_prof_fname $seed_seq_fname > /dev/null 2>&1
    with pyhmmer.easel.MSAFile(
        MSA_fname, digital=False, alphabet=aa_alphabet
    ) as msa_fs:
        loaded_seed: pyhmmer.easel.TextMSA = msa_fs.read()
        # Must convert to a digital MSA according to https://pyhmmer.readthedocs.io/en/stable/examples/msa_to_hmm.html
        loaded_seed = loaded_seed.digitize(alphabet=aa_alphabet)
        builder = pyhmmer.plan7.Builder(alphabet=aa_alphabet)
        background = pyhmmer.plan7.Background(alphabet=aa_alphabet)
        loaded_seed.name = f"{protein_name}_MSA"
        hmm, _, _ = builder.build_msa(loaded_seed, background)

    # The profile exists. We can now do hmmsearch.
    pipeline = pyhmmer.plan7.Pipeline(alphabet=aa_alphabet, background=background)
    with pyhmmer.easel.SequenceFile("", digital=True, alphabet=aa_alphabet) as seq_file:
        hits = pipeline.search_hmm(hmm, seq_file)
    ali = hits[0].domains[0].alignment
    print(ali)

    produced_msa = hits.to_msa(alphabet=aa_alphabet)


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
