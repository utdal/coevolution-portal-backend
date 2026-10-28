import re

from rest_framework import serializers

from .models import (
    PDB,
    APITaskMeta,
    DirectCouplingAnalysis,
    EvolutionSimulation,
    MappedDi,
    MultipleSequenceAlignment,
    SeedSequence,
    StructureContacts,
)
from .modelutils import NdarraySerializerField


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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if ret.get('state') == 'SUCCESS' or ret.get('successful'):
            ret['percent'] = 100.0
            ret['message'] = ""
        return ret


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

    def validate_fasta(self, value):
        """
        Check that the uploaded file is an aligned FASTA: text, at least two records, only letters,
        gaps ('-' or '.'), and every sequence the same length.
        """
        if value is None:
            raise serializers.ValidationError("An MSA file is required.")
        try:
            text = value.read().decode("utf-8")
        except UnicodeDecodeError:
            raise serializers.ValidationError("MSA must be a text FASTA file.")
        finally:
            value.seek(0)

        records = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                records.append([])
            elif not records:
                raise serializers.ValidationError("MSA must be in FASTA format, starting with a header line.")
            else:
                records[-1].append(line)
        sequences = ["".join(record) for record in records]

        if len(sequences) < 2:
            raise serializers.ValidationError("MSA must contain at least 2 sequences.")
        if not all(sequences):
            raise serializers.ValidationError("Every MSA record must have a sequence.")
        if not all(re.fullmatch(r"[A-Za-z.\-]+", sequence) for sequence in sequences):
            raise serializers.ValidationError("MSA sequences may only contain letters and gaps ('-' or '.').")
        lengths = {len(sequence) for sequence in sequences}
        if len(lengths) > 1:
            raise serializers.ValidationError(
                f"MSA sequences must all be the same length (found lengths {min(lengths)} to {max(lengths)}). Is the file aligned?"
            )
        return value


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
    seed = serializers.CharField(max_length=10000)
    msa_name = serializers.CharField(max_length=255, required=False)
    E = serializers.FloatField(required=False)
    perc_max_gaps = serializers.FloatField(required=False)

    def validate_seed(self, value):
        """
        Accept a single FASTA record and normalize it to its header line followed by the sequence on
        one uppercased line.
        """
        lines = [line.strip() for line in value.strip().splitlines() if line.strip()]
        if not lines or not lines[0].startswith(">") or not lines[0][1:].strip():
            raise serializers.ValidationError("Seed must be in FASTA format, starting with a header line such as >my_protein.")
        if any(line.startswith(">") for line in lines[1:]):
            raise serializers.ValidationError("Seed must be a single FASTA record; supply alignments as a Full MSA instead.")

        sequence = "".join(lines[1:]).upper()
        if not sequence:
            raise serializers.ValidationError("Seed contains no sequence.")
        if not sequence.isalpha():
            raise serializers.ValidationError("Seed sequence may only contain amino acid letters.")
        if len(sequence) > 700:
            raise serializers.ValidationError(f"Seed sequence must be at most 700 residues (got {len(sequence)}).")
        return f"{lines[0]}\n{sequence}"

class ComputeDCASerializer(serializers.Serializer):
    msa_id = serializers.UUIDField()
    theta = serializers.FloatField(required=False)

class MapResiduesSerializer(serializers.Serializer):
    dca_id = serializers.UUIDField()
    pdb_id = serializers.CharField(max_length=8)
    chain1 = serializers.CharField(max_length=10)
    chain2 = serializers.CharField(max_length=10)
    auth_chain_id_supplied = serializers.BooleanField()
    auth_residue_id_supplied = serializers.BooleanField()

class GenerateContactsSerializer(serializers.Serializer):
    pdb_id = serializers.CharField(max_length=8)
    ca_only = serializers.BooleanField(required=False)
    threshold = serializers.FloatField(required=False)
    is_cif = serializers.BooleanField(required=False)
    auth_chain_id_supplied = serializers.BooleanField()
    auth_residue_id_supplied = serializers.BooleanField()

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
class EvolutionSimulationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvolutionSimulation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'result_file', 'task_id', 'completed', 'expires',  'error_message', 'percent']
