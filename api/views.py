from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, parsers
from drf_spectacular.utils import extend_schema
import uuid

from .serializers import (
    GenerateContactsSerializer,
    StructureContactsSerializer,
    TaskSerializer,
    GenerateMSASerializer,
    MSASerializer,
    ComputeDCASerializer,
    DCASerializer,
    MapResiduesSerializer,
    MappedDiSerializer,
)
from .models import (
    APITaskMeta,
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
)


def api_home(request):
    return render(request, "index.html")


def hello_world(request):
    return HttpResponse("hello world", status=200)


def demo(request):
    return render(request, "demo.html")


class TaskViewSet(UsersUnexpiredReadOnlyModelViewSet):
    serializer_class = TaskSerializer
    queryset = APITaskMeta.objects.all()


class MSAViewSet(UsersCreateModelMixin, UsersUnexpiredReadOnlyModelViewSet):
    serializer_class = MSASerializer
    parser_classes = [parsers.MultiPartParser]
    queryset = MultipleSequenceAlignment.objects.all()


class DCAViewSet(UsersUnexpiredReadOnlyModelViewSet):
    serializer_class = DCASerializer
    queryset = DirectCouplingAnalysis.objects.all()


class MappedDiViewSet(UsersUnexpiredReadOnlyModelViewSet):
    serializer_class = MappedDiSerializer
    queryset = MappedDi.objects.all()


class StructureContactsViewSet(UsersUnexpiredReadOnlyModelViewSet):
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
                user=get_request_user(request),
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
                user=get_request_user(request),
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
            )

            resp = TaskSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)
