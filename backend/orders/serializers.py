from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    academic_level_name = serializers.CharField(source='academic_level.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'customer_name', 'customer_email',
            'service_name', 'academic_level_name', 'pages', 'words',
            'course_subject', 'total_amount', 'status', 'created_at'
        ]
