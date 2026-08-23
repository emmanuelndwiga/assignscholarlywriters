import logging
import paypalrestsdk
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from .models import Payment
from .serializers import PaymentSerializer, CreatePaymentSerializer
from orders.models import Order

logger = logging.getLogger('payments')

# Configure PayPal
paypalrestsdk.configure({
    'mode': settings.PAYPAL_MODE,
    'client_id': settings.PAYPAL_CLIENT_ID,
    'client_secret': settings.PAYPAL_CLIENT_SECRET,
})


class PaymentCreateThrottle(SimpleRateThrottle):
    scope = 'payment_create'


class PaymentExecuteThrottle(SimpleRateThrottle):
    scope = 'payment_execute'


class CreatePaymentView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PaymentCreateThrottle]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            order = Order.objects.select_related('service', 'currency').get(
                order_id=data['order_id']
            )
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        # Only allow payment creation for pending/confirmed orders
        if order.status not in ('pending', 'confirmed'):
            return Response(
                {'error': f'Order is {order.status} and cannot be paid for.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        currency = order.currency.code if order.currency else data.get('currency_code', 'GBP')

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
            payment_record = Payment.objects.create(
                order=order,
                paypal_order_id=payment.id,
                amount=order.total_amount,
                currency=order.currency,
                status='pending',
                raw_response={'id': payment.id, 'state': payment.state},
            )

            for link in payment.links:
                if link.rel == 'approval_url':
                    return Response({
                        'success': True,
                        'payment_id': payment_record.payment_id,
                        'approval_url': link.href,
                    })

            logger.error('Payment created but no approval URL for order %s', order.order_id)
            return Response({'error': 'No approval URL found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning('PayPal payment creation failed for order %s: %s', order.order_id, payment.error)
            return Response({
                'error': 'Payment creation failed',
                'details': payment.error,
            }, status=status.HTTP_400_BAD_REQUEST)


class ExecutePaymentView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PaymentExecuteThrottle]

    def post(self, request):
        payment_id = request.data.get('paypal_payment_id')
        payer_id = request.data.get('payer_id')
        order_id = request.data.get('order_id')

        if not all([payment_id, payer_id, order_id]):
            return Response(
                {'error': 'Missing required fields: paypal_payment_id, payer_id, order_id'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Look up the payment record — verifies the order_id matches (prevents IDOR)
        try:
            payment_record = Payment.objects.select_related('order', 'order__customer').get(
                paypal_order_id=payment_id,
                order__order_id=order_id,
            )
        except Payment.DoesNotExist:
            logger.warning(
                'Payment execute attempted with mismatched payment_id/order_id: %s/%s',
                payment_id, order_id,
            )
            return Response(
                {'error': 'Payment record not found for this order'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Prevent double-execution
        if payment_record.status == 'paid':
            return Response(
                {'success': True, 'message': 'Payment already processed', 'payment_id': payment_record.payment_id},
            )

        try:
            payment = paypalrestsdk.Payment.find(payment_id)
        except Exception as e:
            logger.exception('PayPal find failed for payment %s', payment_id)
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if payment.execute({'payer_id': payer_id}):
            payment_record.status = 'paid'
            payment_record.paypal_payer_id = payer_id
            if payment.transactions:
                try:
                    sale = payment.transactions[0].related_resources[0].sale
                    payment_record.paypal_transaction_id = sale.id
                except (AttributeError, IndexError):
                    pass
            payment_record.paid_at = timezone.now()
            payment_record.raw_response = {'state': payment.state}
            payment_record.save()

            order = payment_record.order
            order.status = 'confirmed'
            order.save()

            customer = order.customer
            customer.total_orders += 1
            customer.total_spent += payment_record.amount
            customer.save()

            logger.info('Payment executed: P-%s for order %s', payment_record.payment_id, order.order_id)

            return Response({
                'success': True,
                'message': 'Payment successful',
                'payment_id': payment_record.payment_id,
            })
        else:
            logger.warning(
                'PayPal payment execution failed for P-%s: %s',
                payment_record.payment_id, payment.error,
            )
            return Response({
                'error': 'Payment execution failed',
                'details': payment.error,
            }, status=status.HTTP_400_BAD_REQUEST)
