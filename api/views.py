from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers, mixins, viewsets
from drf_spectacular.utils import extend_schema
from .ProSSpeC.calculate_Hamiltonian import calc_Hamiltonian
import pandas as pd
from io import BytesIO
import json
import uuid

from .serializers import (
    GenerateContactsSerializer,
    StructureContactsSerializer,
    TaskSerializer,
    GenerateMSASerializer,
    SeedSerializer,
    MSASerializer,
    ComputeDCASerializer,
    DCASerializer,
    MapResiduesSerializer,
    MappedDiSerializer,
    CalculateHamiltonianSerializer,
    Align2HMMSerializer
)
from .models import (
    APITaskMeta,
    SeedSequence,
    MappedDi,
    MultipleSequenceAlignment,
    DirectCouplingAnalysis,
    StructureContacts,
)
from .tasks import (
    generate_contacts_task,
    generate_msa_task,
    compute_dca_task,
    map_residues_task,
)
from .viewutils import (
    UsersReadOnlyModelViewSet,
    UsersUnexpiredReadOnlyModelViewSet,
    UsersCreateModelMixin,
    get_request_user,
    get_request_session,
)
from .msautils import align_sequences_with_hmm


def api_home(request):
    return render(request, "index.html")


def hello_world(request):
    return HttpResponse("hello world", status=200)


def demo(request):
    return render(request, "demo.html")


class TaskViewSet(UsersUnexpiredReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    queryset = APITaskMeta.objects.all()


class SeedViewSet(UsersCreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SeedSerializer
    parser_classes = [parsers.MultiPartParser]
    queryset = SeedSequence.objects.all()


class MSAViewSet(UsersCreateModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MSASerializer
    parser_classes = [parsers.MultiPartParser]
    queryset = MultipleSequenceAlignment.objects.all()


class DCAViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DCASerializer
    queryset = DirectCouplingAnalysis.objects.all()


class MappedDiViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = MappedDiSerializer
    queryset = MappedDi.objects.all()


class StructureContactsViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = StructureContactsSerializer
    queryset = StructureContacts.objects.all()


class GenerateMsa(APIView):
    serializer_class = GenerateMSASerializer
    throttle_scope = "long_task"

    @extend_schema(
        request=GenerateMSASerializer,
        responses={202: TaskSerializer},
    )
    def post(self, request, format=None):
        params = GenerateMSASerializer(data=request.data)

        if params.is_valid():
            task = generate_msa_task.start(
                params.validated_data.get("seed"),
                params.validated_data.get("msa_name"),
                params.validated_data.get("E"),
                params.validated_data.get("perc_max_gaps"),
                user=get_request_user(request),
                session_key=get_request_session(request),
            )

            resp = TaskSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)


class ComputeDca(APIView):
    serializer_class = ComputeDCASerializer
    throttle_scope = "long_task"

    @extend_schema(
        request=ComputeDCASerializer,
        responses={202: TaskSerializer},
    )
    def post(self, request, format=None):
        params = ComputeDCASerializer(data=request.data)

        if params.is_valid():
            task = compute_dca_task.start(
                params.validated_data.get("msa_id"),
                params.validated_data.get("theta"),
                user=get_request_user(request),
                session_key=get_request_session(request),
            )

            resp = TaskSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)


class MapResidues(APIView):
    serializer_class = MapResiduesSerializer
    throttle_scope = "long_task"

    @extend_schema(
        request=MapResiduesSerializer,
        responses={202: TaskSerializer},
    )
    def post(self, request, format=None):
        params = MapResiduesSerializer(data=request.data)

        if params.is_valid():
            task = map_residues_task.start(
                params.validated_data.get("dca_id"),
                params.validated_data.get("pdb_id"),
                params.validated_data.get("chain1"),
                params.validated_data.get("chain2"),
                params.validated_data.get("auth_chain_id_supplied"),
                user=get_request_user(request),
                session_key=get_request_session(request),
            )

            resp = TaskSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)


class GenerateContacts(APIView):
    serializer_class = GenerateContactsSerializer
    throttle_scope = "long_task"

    @extend_schema(
        request=GenerateContactsSerializer,
        responses={202: TaskSerializer},
    )
    def post(self, request, format=None):
        params = GenerateContactsSerializer(data=request.data)

        if params.is_valid():
            task = generate_contacts_task.start(
                params.validated_data.get("pdb_id"),
                params.validated_data.get("ca_only"),
                params.validated_data.get("threshold"),
                params.validated_data.get("is_cif"),
                user=get_request_user(request),
                session_key=get_request_session(request),
            )

            resp = TaskSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)


class CalculateHamiltonian(APIView):
    serializer_class = CalculateHamiltonianSerializer

    def post(self, request):
        if type(request.data.get("sequences")) is str:
            try:
                sequences = json.loads(request.data.get("sequences"))
                params = CalculateHamiltonianSerializer(data={"sequences":sequences, "local_fields": request.data.get("local_fields"), "couplings": request.data.get("couplings"),'pottsH':None})
            except:
                return Response({"Error": "Invalid json format"}, status=400)
        else:
            params = CalculateHamiltonianSerializer(data=request.data)

        if params.is_valid() or type(request.data.get("sequences")) is str:
            sequences = params.validated_data.get("sequences")
            local_fields = params.validated_data.get("local_fields")
            couplings = params.validated_data.get("couplings")
        
            try:
                lf = pd.read_csv(local_fields, header=None)
                coup = pd.read_csv(couplings, header=None)
            
            except Exception as e:
                return Response({"Error": str(e)},status=status.HTTP_400_BAD_REQUEST)

            try:
                pottsH = calc_Hamiltonian(sequences.values(), coupling_tbl=coup, lf_tbl=lf)
                results = {}
                for idx, item in enumerate(sequences):
                    results[item] = pottsH[idx]
                return Response({
                    "sequences": sequences,
                    "pottsH": results
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"Error": str(e)},status=status.HTTP_400_BAD_REQUEST)


class AlignSequences2HMM(APIView):
    serializer_class = Align2HMMSerializer

    def post(self, request):

        if request.data.get("json_input") == "null":
            json_input = None
        elif type(request.data.get("json_input")) is str:
            try:
                json_input = json.loads(request.data.get("json_input"))
            except:
                return Response({"Error": "Invalid json format"}, status=400)
        else:
            json_input = request.data.get("json_input")
        
        if request.data.get("fasta_input") == "null":
            fasta_input = None
        else:
            fasta_input = request.data.get("fasta_input")
        

        params = Align2HMMSerializer(data={"json_input": json_input, "fasta_input": fasta_input, "hmm_input": request.data.get("hmm_input"), "aligned_sequences": request.data.get("aligned_sequences")})

        if params.is_valid():
            json_input = params.validated_data.get("json_input")
            fasta_input = params.validated_data.get("fasta_input")
            if fasta_input:
                fasta_input = fasta_input.file
            hmm_file = params.validated_data.get("hmm_input")
            hmm_file = BytesIO(hmm_file.file.read())
            hmm_copy = BytesIO(hmm_file.getvalue())
            hmm_file.seek(0)

            results = {}
            if  json_input is None and fasta_input is None:
                return Response("Error: No sequences were provided", status=status.HTTP_400_BAD_REQUEST)
            else:
                if json_input:
                    try:
                        sequences = list(json_input.values())
                        headers = list(json_input.keys())
                        aligned = align_sequences_with_hmm(hmm=hmm_file, sequences=sequences,headers=headers)
                        results = results | aligned

                    except Exception as e:
                        return Response({"Error": str(e)},status=status.HTTP_400_BAD_REQUEST)

                if fasta_input:
                    try:
                        aligned = align_sequences_with_hmm(hmm=hmm_copy, sequences=fasta_input)
                        results = results | aligned

                    except Exception as e:
                        return Response({"Error": str(e)},status=status.HTTP_400_BAD_REQUEST)
                
                return Response({"aligned_sequences": results}, status=status.HTTP_200_OK)
        else:
            return Response("Error", status=status.HTTP_400_BAD_REQUEST)