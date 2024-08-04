from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import hello_world, demo, ListJobs, ViewJob, GenerateMsa, ComputeDca, ListMsas, ViewMsa, ListDcas, ViewDca

urlpatterns = [
    path('hello/', hello_world, name='hello'),
    path('demo/', demo, name='demo'),

    path('jobs/', ListJobs.as_view()),
    path('jobs/<str:pk>/', ViewJob.as_view()),

    path('generate-msa/', GenerateMsa.as_view()),
    path('compute-dca/', ComputeDca.as_view()),

    path('msas/', ListMsas.as_view()),
    path('msas/<str:pk>', ViewMsa.as_view()),

    path('dcas/', ListDcas.as_view()),
    path('dcas/<str:pk>', ViewDca.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
