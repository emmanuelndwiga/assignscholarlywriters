from rest_framework import serializers
from .models import PricingSeason, DeadlineMultiplier, PriceConfig


class PricingSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingSeason
        fields = ['id', 'name', 'season_type', 'start_date', 'end_date', 'global_multiplier', 'is_active']


class DeadlineMultiplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeadlineMultiplier
        fields = ['id', 'name', 'days', 'multiplier', 'order']


class PriceConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceConfig
        fields = ['id', 'name', 'words_per_page', 'base_currency', 'is_active']
