from rest_framework import serializers

from .modelutils import NdarraySerializerField
from .models import (
    APITaskMeta,
    MappedDi,
    SeedSequence,
    MultipleSequenceAlignment,
    DirectCouplingAnalysis,
    StructureContacts,
)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = APITaskMeta
        fields = [
            "id",
            "user",
            "state",
            "name",
            "time_started",
            "time_ended",
            "expires",
            "message",
            "percent",
            "successful",
        ]


class SeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedSequence
        fields = [
            "id",
            "user",
            "created",
            "expires",
            "name",
            "fasta"
        ]
        read_only_fields = ["id", "user", "created", "expires"]


class MSASerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleSequenceAlignment
        fields = [
            "id",
            "user",
            "created",
            "expires",
            "seed",
            "fasta",
            "depth",
            "cols",
            "quality",
        ]
        read_only_fields = ["id", "user", "created", "expires"]


class DCASerializer(serializers.ModelSerializer):
    ranked_di = NdarraySerializerField(required=False)

    class Meta:
        model = DirectCouplingAnalysis
        fields = ["id", "user", "created", "expires", "m_eff", "ranked_di"]


class MappedDiSerializer(serializers.ModelSerializer):
    mapped_di = NdarraySerializerField(required=False)

    class Meta:
        model = MappedDi
        fields = [
            "id",
            "user",
            "created",
            "expires",
            "protein_name",
            "seed",
            "dca",
            "mapped_di",
        ]


class StructureContactsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StructureContacts
        fields = [
            "id",
            "user",
            "created",
            "expires",
            "pdb_id",
            "ca_only",
            "threshold",
            "contacts",
        ]


class GenerateMSASerializer(serializers.Serializer):
    seed = serializers.CharField(max_length=700)
    msa_name = serializers.CharField(max_length=255, required=False)
    E = serializers.FloatField()
    max_gaps = serializers.IntegerField()

class ComputeDCASerializer(serializers.Serializer):
    msa_id = serializers.UUIDField()
    theta = serializers.FloatField()

class MapResiduesSerializer(serializers.Serializer):
    dca_id = serializers.UUIDField()
    pdb_id = serializers.CharField(max_length=8)
    chain1 = serializers.CharField(max_length=10)
    chain2 = serializers.CharField(max_length=10)


class GenerateContactsSerializer(serializers.Serializer):
    pdb_id = serializers.CharField(max_length=8)
    ca_only = serializers.BooleanField()
    threshold = serializers.FloatField()
