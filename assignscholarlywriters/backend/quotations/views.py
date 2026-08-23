import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import SimpleRateThrottle
from django.db import transaction
from .models import Quotation, QuotationAttachment
from .serializers import (
    QuotationCreateSerializer,
    QuotationListSerializer,
    QuotationDetailSerializer,
    CalculatePriceSerializer,
)
from services.models import ServiceType, AcademicLevel
from pricing.models import DeadlineMultiplier, PriceConfig, PricingSeason
from pricing.engine import PricingEngine
from currencies.models import Currency
from customers.models import Customer
from notifications.services import notify_quotation

logger = logging.getLogger('quotations')

ALLOWED_UPLOAD_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB


class QuotationCreateThrottle(SimpleRateThrottle):
    scope = 'quotation_create'


class CalculatePriceThrottle(SimpleRateThrottle):
    scope = 'calculate_price'


class CalculatePriceView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [CalculatePriceThrottle]

    def post(self, request):
        serializer = CalculatePriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            service = ServiceType.objects.get(id=data['service_id'], is_active=True)
            level = AcademicLevel.objects.get(id=data['academic_level_id'], is_active=True)
            deadline = DeadlineMultiplier.objects.get(id=data['deadline_id'], is_active=True)
        except (ServiceType.DoesNotExist, AcademicLevel.DoesNotExist,
                DeadlineMultiplier.DoesNotExist) as e:
            return Response(
                {'error': f'Invalid parameter: {e}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        result = PricingEngine.calculate(
            service, level, data['pages'], deadline, data['currency_code']
        )

        return Response({'success': True, 'data': result})


class CreateQuotationView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [QuotationCreateThrottle]

    @transaction.atomic
    def post(self, request):
        serializer = QuotationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            service = ServiceType.objects.get(id=data['service_id'], is_active=True)
            level = AcademicLevel.objects.get(id=data['academic_level_id'], is_active=True)
            deadline = DeadlineMultiplier.objects.get(id=data['deadline_id'], is_active=True)
            currency = Currency.objects.get(code=data['currency_code'], is_active=True)
        except (ServiceType.DoesNotExist, AcademicLevel.DoesNotExist,
                DeadlineMultiplier.DoesNotExist, Currency.DoesNotExist) as e:
            return Response(
                {'error': f'Invalid parameter: {e}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        config = PriceConfig.get_active()
        words = data['pages'] * config.words_per_page

        result = PricingEngine.calculate(service, level, data['pages'], deadline, data['currency_code'])

        customer = Customer.get_or_create_from_data(
            name=data['customer_name'],
            email=data['customer_email'],
            phone=data.get('customer_phone', ''),
            whatsapp=data.get('customer_whatsapp', ''),
        )

        current_season = PricingSeason.get_current()

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

        # Handle file uploads with validation
        files = request.FILES.getlist('files')
        for f in files:
            ext = '.' + f.name.rsplit('.', 1)[-1].lower() if '.' in f.name else ''
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                return Response(
                    {'error': f'File type not allowed: {ext}. Allowed: {", ".join(ALLOWED_UPLOAD_EXTENSIONS)}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if f.size > MAX_UPLOAD_SIZE:
                return Response(
                    {'error': f'File too large: {f.name} ({f.size} bytes). Max: {MAX_UPLOAD_SIZE} bytes.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            QuotationAttachment.objects.create(
                quotation=quotation,
                file=f,
                original_filename=f.name,
            )

        logger.info('Quotation created: Q-%s by %s', quotation.request_id, customer.email)

        try:
            notify_quotation(quotation)
        except Exception:
            logger.exception('Failed to send notifications for Q-%s', quotation.request_id)

        return Response({
            'success': True,
            'quotation': QuotationDetailSerializer(quotation).data,
            'message': 'Quotation request submitted successfully. We will review and get back to you shortly.',
        }, status=status.HTTP_201_CREATED)


class QuotationListView(generics.ListAPIView):
    """List quotations — requires admin login."""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = QuotationListSerializer

    def get_queryset(self):
        qs = Quotation.objects.select_related(
            'customer', 'service', 'academic_level', 'deadline', 'currency'
        ).all()

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        email = self.request.query_params.get('email')
        if email:
            qs = qs.filter(customer__email__icontains=email)

        return qs


class QuotationDetailView(generics.RetrieveAPIView):
    """Retrieve a single quotation — requires admin login."""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = QuotationDetailSerializer
    lookup_field = 'request_id'

    def get_queryset(self):
        return Quotation.objects.select_related(
            'customer', 'service', 'academic_level', 'deadline', 'currency', 'pricing_season'
        ).prefetch_related('attachments')
