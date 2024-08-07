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
    TaskSerializer,
    GenerateMSASerializer,
    MSASerializer,
    ComputeDCASerializer,
    DCASerializer,
)
from .models import APITaskMeta, MultipleSequenceAlignment, DirectCouplingAnalysis
from .tasks import generate_msa_task, compute_dca_task
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
