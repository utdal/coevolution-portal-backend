from django.db import models
from django.contrib.auth.models import User

from .modelutils import NdarrayField, get_user_spesific_path


class CeleryTaskMeta(models.Model):
    id = models.UUIDField(primary_key=True)
    state = models.CharField(max_length=20, default="UNKNOWN")
    name = models.CharField(max_length=255, blank=True)
    time_started = models.DateTimeField(auto_now_add=True)
    time_ended = models.DateTimeField(null=True)
    message = models.CharField(max_length=50, blank=True)
    percent = models.FloatField(default=0)
    successful = models.BooleanField(default=False)


class APITaskMeta(CeleryTaskMeta):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)


class APIDataObject(models.Model):
    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField()


def get_msa_upload_to(instance, filename):
    return get_user_spesific_path(
        filename, instance.user, subfolder="msa", suffix=".fasta"
    )


class MultipleSequenceAlignment(APIDataObject):
    class Qualities(models.IntegerChoices):
        NA = 0
        AWFUL = 1
        BAD = 2
        OKAY = 3
        GOOD = 4
        GREAT = 5

    fasta = models.FileField(upload_to=get_msa_upload_to, null=True, unique=True)
    depth = models.IntegerField(default=0)
    cols = models.IntegerField(default=0)
    quality = models.IntegerField(choices=Qualities, default=Qualities.NA)


class DirectCouplingAnalysis(APIDataObject):
    e_ij = NdarrayField(null=True)
    h_i = NdarrayField(null=True)
    ranked_di = NdarrayField(null=True)
    m_eff = models.IntegerField(null=True)


class ContactMap(APIDataObject):
    pdb = models.CharField(max_length=50, blank=True)
    coupling_results = models.ForeignKey(
        DirectCouplingAnalysis, on_delete=models.CASCADE, null=True
    )
    map = NdarrayField(null=True)
