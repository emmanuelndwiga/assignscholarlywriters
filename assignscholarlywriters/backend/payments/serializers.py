from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'order', 'paypal_order_id',
            'amount', 'currency', 'status', 'payment_method',
            'created_at', 'paid_at'
        ]


class CreatePaymentSerializer(serializers.Serializer):
    order_id = serializers.CharField()
    currency_code = serializers.CharField(max_length=3, default='GBP')
