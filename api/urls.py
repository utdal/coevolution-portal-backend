from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns

from .views import (
    hello_world,
    demo,
    ListTasks,
    ViewTask,
    GenerateMsa,
    UploadMsa,
    ComputeDca,
    ListMsas,
    ViewMsa,
    ListDcas,
    ViewDca,
)

urlpatterns = [
    path("hello/", hello_world, name="hello"),
    path("demo/", demo, name="demo"),
    path("tasks/", ListTasks.as_view()),
    path("tasks/<str:pk>/", ViewTask.as_view()),
    path("generate-msa/", GenerateMsa.as_view()),
    path("upload-msa/", UploadMsa.as_view()),
    path("compute-dca/", ComputeDca.as_view()),
    path("msas/", ListMsas.as_view()),
    path("msas/<str:pk>", ViewMsa.as_view()),
    path("dcas/", ListDcas.as_view()),
    path("dcas/<str:pk>", ViewDca.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
