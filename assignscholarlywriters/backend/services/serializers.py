from rest_framework import serializers
from .models import AcademicLevel, ServiceType


class AcademicLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicLevel
        fields = ['id', 'name', 'slug', 'multiplier', 'order']


class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ['id', 'name', 'slug', 'description', 'base_price_per_page', 'order']
