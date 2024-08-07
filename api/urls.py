from django.urls import path, include
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import (
    api_home,
    hello_world,
    demo,
    TaskViewSet,
    MSAViewSet,
    DCAViewSet,
    GenerateMsa,
    ComputeDca,
)

urlpatterns = [
    # Basic pages
    path("", api_home),
    path("hello/", hello_world),
    path("demo/", demo),
    # Login /logout
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # API Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    # API endpoints
    path("generate-msa/", GenerateMsa.as_view()),
    path("compute-dca/", ComputeDca.as_view()),
]

router = DefaultRouter()
router.register("tasks", TaskViewSet, basename='task')
router.register("msas", MSAViewSet, basename='msa')
router.register("dcas", DCAViewSet, basename='dca')

urlpatterns += router.urls
