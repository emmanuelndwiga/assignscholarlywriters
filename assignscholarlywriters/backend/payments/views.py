import paypalrestsdk
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer
from orders.models import Order

# Configure PayPal
paypalrestsdk.configure({
    'mode': settings.PAYPAL_MODE,
    'client_id': settings.PAYPAL_CLIENT_ID,
    'client_secret': settings.PAYPAL_CLIENT_SECRET,
})


class CreatePaymentView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = Order.objects.get(order_id=data['order_id'])
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        currency = order.currency.code if order.currency else data['currency_code']

        payment = paypalrestsdk.Payment({
            'intent': 'sale',
            'payer': {'payment_method': 'paypal'},
            'redirect_urls': {
                'return_url': f"{settings.FRONTEND_URL}/pricing.html?payment=success&order={order.order_id}",
                'cancel_url': f"{settings.FRONTEND_URL}/pricing.html?payment=cancelled&order={order.order_id}",
            },
            'transactions': [{
                'item_list': {
                    'items': [{
                        'name': f'Academic Writing - {order.service.name if order.service else "Service"}',
                        'sku': order.order_id,
                        'price': str(order.total_amount),
                        'currency': currency,
                        'quantity': 1,
                    }]
                },
                'amount': {
                    'total': str(order.total_amount),
                    'currency': currency,
                },
                'description': f'ScholarlyWriters Order #{order.order_id}',
            }]
        })

        if payment.create():
            # Store payment record
            payment_record = Payment.objects.create(
                order=order,
                paypal_order_id=payment.id,
                amount=order.total_amount,
                currency=order.currency,
                status='pending',
                raw_response={'id': payment.id, 'state': payment.state},
            )

            # Get approval URL
            for link in payment.links:
                if link.rel == 'approval_url':
                    return Response({
                        'success': True,
                        'payment_id': payment_record.payment_id,
                        'approval_url': link.href,
                    })

            return Response({'error': 'No approval URL found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response({
                'error': 'Payment creation failed',
                'details': payment.error,
            }, status=status.HTTP_400_BAD_REQUEST)


class ExecutePaymentView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        payment_id = request.data.get('paypal_payment_id')
        payer_id = request.data.get('payer_id')
        order_id = request.data.get('order_id')

        if not all([payment_id, payer_id, order_id]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if payment.execute({'payer_id': payer_id}):
            # Update payment record
            try:
                payment_record = Payment.objects.get(paypal_order_id=payment_id)
                payment_record.status = 'paid'
                payment_record.paypal_payer_id = payer_id
                if payment.transactions:
                    payment_record.paypal_transaction_id = payment.transactions[0].related_resources[0].sale.id if hasattr(payment.transactions[0].related_resources[0], 'sale') else ''
                payment_record.paid_at = timezone.now()
                payment_record.raw_response = {'state': payment.state}
                payment_record.save()

                # Update order
                order = payment_record.order
                order.status = 'confirmed'
                order.save()

                # Update customer stats
                customer = order.customer
                customer.total_orders += 1
                customer.total_spent += payment_record.amount
                customer.save()

                return Response({
                    'success': True,
                    'message': 'Payment successful',
                    'payment_id': payment_record.payment_id,
                })
            except Payment.DoesNotExist:
                return Response({'error': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({
                'error': 'Payment execution failed',
                'details': payment.error,
            }, status=status.HTTP_400_BAD_REQUEST)
