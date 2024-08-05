from rest_framework import serializers

from .modelutils import NdarraySerializerField
from .models import APITask, MSA, DirectCouplingResults, ContactMap


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = APITask
        fields = ['id', 'user', 'state', 'time_started',
                  'time_ended', 'message', 'percent', 'successful']


class MSASerializer(serializers.ModelSerializer):
    class Meta:
        model = MSA
        fields = ['id', 'user', 'expires', 'fasta', 'depth', 'cols', 'quality']


class DirectCouplingSerializer(serializers.ModelSerializer):
    ranked_di = NdarraySerializerField()

    class Meta:
        model = DirectCouplingResults
        fields = ['id', 'user', 'm_eff', 'ranked_di']


class GenerateMSASerializer(serializers.Serializer):
    seed = serializers.CharField(max_length=700)
    msa_name = serializers.CharField(max_length=100, required=False)
    prereqs = serializers.ListField(
        child=serializers.UUIDField(), required=False)


class UploadMSASerializer(serializers.ModelSerializer):
    class Meta:
        model = MSA
        fields = ['fasta']


class ComputeDCASerializer(serializers.Serializer):
    msa_id = serializers.UUIDField()
    prereqs = serializers.ListField(
        child=serializers.UUIDField(), required=False)
