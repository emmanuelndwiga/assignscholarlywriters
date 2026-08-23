from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import Sample
from .serializers import SampleSerializer


class SampleListView(generics.ListAPIView):
    serializer_class = SampleSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        return Sample.objects.filter(is_active=True)


class SampleDetailView(generics.RetrieveAPIView):
    serializer_class = SampleSerializer
    permission_classes = [AllowAny]
    lookup_field = 'pk'

    def get_queryset(self):
        return Sample.objects.filter(is_active=True)
