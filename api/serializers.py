from rest_framework import serializers

from .modelutils import NdarraySerializerField
from .models import APITaskMeta, MappedDi, MultipleSequenceAlignment, DirectCouplingAnalysis


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


class MSASerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleSequenceAlignment
        fields = [
            "id",
            "user",
            "created",
            "expires",
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
        fields = ["id", "user", "created", "expires", "protein_name", "seed", "dca", "mapped_di"]


class GenerateMSASerializer(serializers.Serializer):
    seed = serializers.CharField(max_length=700)
    msa_name = serializers.CharField(max_length=255, required=False)


class ComputeDCASerializer(serializers.Serializer):
    msa_id = serializers.UUIDField()


class MapResiduesSerializer(serializers.Serializer):
    dca_id = serializers.UUIDField()
    pdb_id = serializers.CharField(max_length=8)
    seed_id = serializers.UUIDField()

class StructureContactsSerializer(serializers.Serializer):
    pdb_id = serializers.CharField(max_length=8)
    ca_only = serializers.BooleanField()
    threshold = serializers.FloatField()
