from django.urls import path
from .views import hello_world, demo, job_status, job_result, get_msa, get_DI_pairs

urlpatterns = [
    path('hello/', hello_world, name='hello'),
    path('demo/', demo, name='demo'),
    path('jobs/<str:id>/', job_status, name='job-status'),
    path('jobs/<str:id>/result/', job_result, name='job-result'),

    path('msa/', get_msa, name='get-msa'),
    path('di/', get_DI_pairs, name='get-di-pairs'),
]
