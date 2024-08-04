from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, status
import uuid

from .serializers import JobSerializer, GenerateMSASerializer, MSASerializer, ComputeDCASerializer, DirectCouplingSerializer
from .models import APITask, MSA, DirectCouplingResults, ContactMap
from .tasks import generate_msa_task, compute_dca_task


def hello_world(request):
    return HttpResponse('hello world', status=200)


def demo(request):
    return render(request, 'demo.html')


class ListJobs(generics.ListAPIView):
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return APITask.objects.filter(user=self.request.user)


class ViewJob(generics.RetrieveAPIView):
    queryset = APITask.objects.all()
    serializer_class = JobSerializer


class GenerateMsa(APIView):
    serializer_class = GenerateMSASerializer
    throttle_scope = 'long_task'

    def post(self, request, format=None):
        params = GenerateMSASerializer(data=request.data)

        if params.is_valid():
            seed = params.validated_data.get('seed')
            msaName = params.validated_data.get('msa_name', str(uuid.uuid4()))
            task = generate_msa_task.start(seed, msaName, user=request.user)

            resp = JobSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)


class ComputeDca(APIView):
    serializer_class = ComputeDCASerializer
    throttle_scope = 'long_task'

    def post(self, request, format=None):
        params = ComputeDCASerializer(data=request.data)

        if params.is_valid():
            msa_id = params.validated_data.get('msa_id')
            prereqs = params.validated_data.get('prereqs')
            task = compute_dca_task.start(
                msa_id, user=request.user, prereqs=prereqs)

            resp = JobSerializer(task)
            return Response(resp.data, status=status.HTTP_202_ACCEPTED)
        return Response(params.errors, status=status.HTTP_400_BAD_REQUEST)


class ListMsas(generics.ListAPIView):
    serializer_class = MSASerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MSA.objects.filter(user=self.request.user)


class ViewMsa(generics.RetrieveAPIView):
    queryset = MSA.objects.all()
    serializer_class = MSASerializer


class ListDcas(generics.ListAPIView):
    serializer_class = DirectCouplingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DirectCouplingResults.objects.filter(user=self.request.user)


class ViewDca(generics.RetrieveAPIView):
    queryset = DirectCouplingResults.objects.all()
    serializer_class = DirectCouplingSerializer
