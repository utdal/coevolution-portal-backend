from rest_framework import serializers

from .modelutils import NdarraySerializerField
from .models import (
    APITaskMeta,
    MappedDi,
    SeedSequence,
    PDB,
    MultipleSequenceAlignment,
    DirectCouplingAnalysis,
    StructureContacts,
)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = APITaskMeta
        fields = [
            "id",
            "session_key",
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


class PDBSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDB
        fields = [
            "id",
            "user",
            "created",
            "expires",
            "name",
            "pdb_id",
            "pdb_file",
            "file_type"
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
    E = serializers.FloatField(required=False)
    perc_max_gaps = serializers.FloatField(required=False)

class ComputeDCASerializer(serializers.Serializer):
    msa_id = serializers.UUIDField()
    theta = serializers.FloatField(required=False)

class MapResiduesSerializer(serializers.Serializer):
    dca_id = serializers.UUIDField()
    pdb_id = serializers.CharField(max_length=8)
    chain1 = serializers.CharField(max_length=10)
    chain2 = serializers.CharField(max_length=10)
    auth_chain_id_supplied = serializers.BooleanField()


class GenerateContactsSerializer(serializers.Serializer):
    pdb_id = serializers.CharField(max_length=8)
    ca_only = serializers.BooleanField(required=False)
    threshold = serializers.FloatField(required=False)
    is_cif = serializers.BooleanField(required=False)

class CalculateHamiltonianSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False, allow_null=True) # used to pull precomputed couplings and local fields
    sequences = serializers.JSONField(required =True)  # headers are keys and sequences are values
    local_fields = serializers.FileField(required=False, allow_null=True)  # must be csv w/no headers or indices
    couplings = serializers.FileField(required=False, allow_null=True)  # must be csv w/no headers or indices
    pottsH = serializers.JSONField(required=False, allow_null=True)  # headers are keys and Hamiltonian value is the values

class Align2HMMSerializer(serializers.Serializer):
    json_input = serializers.JSONField(required=False, allow_null=True)  # headers are keys and sequences are values
    fasta_input = serializers.FileField(required=False, allow_null=True)  # file must be fasta format
    hmm_input =  serializers.FileField(required=True)  # file must be .hmm format
    aligned_sequences = serializers.JSONField(required=False, allow_null=True)  # headers are keys and sequences are values
