from rest_framework import serializers

from .modelutils import NdarraySerializerField
from .models import APITaskMeta, MultipleSequenceAlignment, DirectCouplingAnalysis


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = APITaskMeta
        fields = [
            "id",
            "user",
            "state",
            "time_started",
            "time_ended",
            "message",
            "percent",
            "successful",
        ]


class MSASerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleSequenceAlignment
        fields = ["id", "user", "expires", "fasta", "depth", "cols", "quality"]


class DCASerializer(serializers.ModelSerializer):
    ranked_di = NdarraySerializerField()

    class Meta:
        model = DirectCouplingAnalysis
        fields = ["id", "user", "m_eff", "ranked_di"]


class GenerateMSASerializer(serializers.Serializer):
    seed = serializers.CharField(max_length=700)
    msa_name = serializers.CharField(max_length=100, required=False)
    prereqs = serializers.ListField(child=serializers.UUIDField(), required=False)


class UploadMSASerializer(serializers.ModelSerializer):
    class Meta:
        model = MultipleSequenceAlignment
        fields = ["fasta"]


class ComputeDCASerializer(serializers.Serializer):
    msa_id = serializers.UUIDField()
    prereqs = serializers.ListField(child=serializers.UUIDField(), required=False)
