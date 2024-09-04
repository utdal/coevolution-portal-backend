from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import celery
from functools import partial

from .modelutils import (
    NdarrayField,
    get_user_spesific_path,
    get_random_uuid,
    get_future_date,
)


class CeleryTaskMeta(models.Model):
    id = models.UUIDField(primary_key=True)
    state = models.CharField(max_length=20, default="UNKNOWN")
    name = models.CharField(max_length=255, blank=True)
    time_started = models.DateTimeField(auto_now_add=True)
    time_ended = models.DateTimeField(null=True)
    message = models.CharField(max_length=255, blank=True)
    percent = models.FloatField(default=0)
    successful = models.BooleanField(default=False)

    def wait_for_completion(self):
        if self.successful:
            return
        result = celery.current_app.AsyncResult(str(self.id))
        result.get(disable_sync_subtasks=False)  # Not recommended! Not sure a better way...


class APITaskMeta(CeleryTaskMeta):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    expires = models.DateTimeField(
        default=partial(get_future_date, settings.TASK_EXPIRATION)
    )


# Stores data created by a user with the API
class APIDataObject(models.Model):
    id = models.UUIDField(primary_key=True, default=get_random_uuid)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(
        default=partial(get_future_date, settings.DATA_EXPIRATION)
    )


class SeedSequence(APIDataObject):
    name = models.CharField(max_length=200)
    fasta = models.FileField(
        upload_to=partial(get_user_spesific_path, subfolder="seeds", suffix=".fasta")
    )


class MultipleSequenceAlignment(APIDataObject):
    class Qualities(models.IntegerChoices):
        NA = 0
        AWFUL = 1
        BAD = 2
        OKAY = 3
        GOOD = 4
        GREAT = 5

    seed = models.ForeignKey(SeedSequence, on_delete=models.SET_NULL, null=True)
    fasta = models.FileField(
        upload_to=partial(get_user_spesific_path, subfolder="msa", suffix=".fasta"),
        null=True,
    )
    # Not sure a good way to auto-update depth, cols, etc...
    depth = models.IntegerField(default=0)
    cols = models.IntegerField(default=0)
    quality = models.IntegerField(choices=Qualities, default=Qualities.NA)


class DirectCouplingAnalysis(APIDataObject):
    msa = models.ForeignKey(MultipleSequenceAlignment, on_delete=models.SET_NULL, null=True)
    e_ij = NdarrayField(null=True)
    h_i = NdarrayField(null=True)
    ranked_di = NdarrayField(null=True)
    m_eff = models.IntegerField(null=True)


class MappedDi(APIDataObject):
    protein_name = models.CharField(max_length=200)
    seed = models.ForeignKey(SeedSequence, on_delete=models.CASCADE)
    dca = models.ForeignKey(DirectCouplingAnalysis, on_delete=models.CASCADE)
    mapped_di = NdarrayField()


class StructureContacts(APIDataObject):
    pdb_id = models.CharField(max_length=8)
    ca_only = models.BooleanField()
    threshold = models.IntegerField()
    contacts = models.JSONField()