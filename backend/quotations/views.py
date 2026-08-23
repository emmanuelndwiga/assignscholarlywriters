from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from .models import Quotation, QuotationAttachment
from .serializers import (
    QuotationCreateSerializer,
    QuotationListSerializer,
    QuotationDetailSerializer,
    CalculatePriceSerializer,
)
from services.models import ServiceType, AcademicLevel
from pricing.models import DeadlineMultiplier
from pricing.engine import PricingEngine
from currencies.models import Currency
from customers.models import Customer
from notifications.services import notify_quotation


class CalculatePriceView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CalculatePriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = ServiceType.objects.get(id=data['service_id'])
        level = AcademicLevel.objects.get(id=data['academic_level_id'])
        deadline = DeadlineMultiplier.objects.get(id=data['deadline_id'])
        currency_code = data['currency_code']

        result = PricingEngine.calculate(service, level, data['pages'], deadline, currency_code)

        return Response({
            'success': True,
            'data': result,
        })


class CreateQuotationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def post(self, request):
        serializer = QuotationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = ServiceType.objects.get(id=data['service_id'])
        level = AcademicLevel.objects.get(id=data['academic_level_id'])
        deadline = DeadlineMultiplier.objects.get(id=data['deadline_id'])
        currency = Currency.objects.get(code=data['currency_code'])
        config = __import__('pricing.models', fromlist=['PriceConfig']).PriceConfig.get_active()

        words = data['pages'] * config.words_per_page

        result = PricingEngine.calculate(service, level, data['pages'], deadline, data['currency_code'])

        customer = Customer.get_or_create_from_data(
            name=data['customer_name'],
            email=data['customer_email'],
            phone=data.get('customer_phone', ''),
            whatsapp=data.get('customer_whatsapp', ''),
        )

        current_season = __import__('pricing.models', fromlist=['PricingSeason']).PricingSeason.get_current()

        quotation = Quotation.objects.create(
            customer=customer,
            service=service,
            academic_level=level,
            pages=data['pages'],
            words=words,
            deadline=deadline,
            currency=currency,
            course_subject=data.get('course_subject', ''),
            specifications=data.get('specifications', ''),
            base_price=result['base_price'],
            estimated_price=result['final_price'],
            exchange_rate_used=result['exchange_rate'],
            pricing_season=current_season,
            status='pending',
        )

        # Handle file uploads
        files = request.FILES.getlist('files')
        for f in files:
            QuotationAttachment.objects.create(
                quotation=quotation,
                file=f,
                original_filename=f.name,
            )

        # Send notifications asynchronously would be better, but sync for now
        try:
            notify_quotation(quotation)
        except Exception:
            pass  # Don't fail the request if notifications fail

        return Response({
            'success': True,
            'quotation': QuotationDetailSerializer(quotation).data,
            'message': 'Quotation request submitted successfully. We will review and get back to you shortly.',
        }, status=status.HTTP_201_CREATED)


class QuotationListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = QuotationListSerializer

    def get_queryset(self):
        email = self.request.query_params.get('email')
        if email:
            return Quotation.objects.filter(customer__email=email)
        return Quotation.objects.none()


class QuotationDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = QuotationDetailSerializer
    lookup_field = 'request_id'
    queryset = Quotation.objects.all()
