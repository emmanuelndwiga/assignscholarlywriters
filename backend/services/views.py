from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import AcademicLevel, ServiceType
from .serializers import AcademicLevelSerializer, ServiceTypeSerializer


class AcademicLevelListView(generics.ListAPIView):
    queryset = AcademicLevel.objects.filter(is_active=True)
    serializer_class = AcademicLevelSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class ServiceTypeListView(generics.ListAPIView):
    queryset = ServiceType.objects.filter(is_active=True)
    serializer_class = ServiceTypeSerializer
    permission_classes = [AllowAny]
    pagination_class = None
