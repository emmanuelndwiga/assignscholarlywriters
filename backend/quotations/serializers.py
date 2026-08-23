from rest_framework import serializers
from .models import Quotation, QuotationAttachment
from customers.models import Customer
from services.serializers import AcademicLevelSerializer, ServiceTypeSerializer
from pricing.serializers import DeadlineMultiplierSerializer
from currencies.serializers import CurrencySerializer


class QuotationAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationAttachment
        fields = ['id', 'file', 'original_filename', 'uploaded_at']
        read_only_fields = ['original_filename', 'uploaded_at']


class QuotationCreateSerializer(serializers.Serializer):
    # Customer info
    customer_name = serializers.CharField(max_length=200)
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    customer_whatsapp = serializers.CharField(max_length=30, required=False, allow_blank=True)

    # Service details
    service_id = serializers.IntegerField()
    academic_level_id = serializers.IntegerField()
    pages = serializers.IntegerField(min_value=1, max_value=5000)
    deadline_id = serializers.IntegerField()
    currency_code = serializers.CharField(max_length=3, default='GBP')
    course_subject = serializers.CharField(max_length=200, required=False, allow_blank=True)
    specifications = serializers.CharField(required=False, allow_blank=True)

    def validate_service_id(self, value):
        from services.models import ServiceType
        if not ServiceType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive service type.")
        return value

    def validate_academic_level_id(self, value):
        from services.models import AcademicLevel
        if not AcademicLevel.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive academic level.")
        return value

    def validate_deadline_id(self, value):
        from pricing.models import DeadlineMultiplier
        if not DeadlineMultiplier.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive deadline.")
        return value

    def validate_currency_code(self, value):
        from currencies.models import Currency
        if not Currency.objects.filter(code=value.upper(), is_active=True).exists():
            raise serializers.ValidationError("Invalid or inactive currency.")
        return value.upper()


class QuotationListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    academic_level_name = serializers.CharField(source='academic_level.name', read_only=True)
    deadline_name = serializers.CharField(source='deadline.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'request_id', 'customer_name', 'customer_email',
            'service_name', 'academic_level_name', 'pages', 'words',
            'deadline_name', 'currency_code', 'currency_symbol',
            'course_subject', 'estimated_price', 'status',
            'created_at', 'expires_at'
        ]


class QuotationDetailSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField()
    service = ServiceTypeSerializer(read_only=True)
    academic_level = AcademicLevelSerializer(read_only=True)
    deadline = DeadlineMultiplierSerializer(read_only=True)
    currency = CurrencySerializer(read_only=True)
    attachments = QuotationAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'request_id', 'customer', 'service', 'academic_level',
            'pages', 'words', 'deadline', 'currency', 'course_subject',
            'specifications', 'estimated_price', 'base_price',
            'exchange_rate_used', 'pricing_season', 'status',
            'admin_notes', 'final_price', 'attachments',
            'created_at', 'updated_at', 'expires_at'
        ]

    def get_customer(self, obj):
        return {
            'name': obj.customer.name,
            'email': obj.customer.email,
            'phone': obj.customer.phone,
            'whatsapp': obj.customer.whatsapp,
        }


class CalculatePriceSerializer(serializers.Serializer):
    service_id = serializers.IntegerField()
    academic_level_id = serializers.IntegerField()
    pages = serializers.IntegerField(min_value=1, max_value=5000)
    deadline_id = serializers.IntegerField()
    currency_code = serializers.CharField(max_length=3, default='GBP')
