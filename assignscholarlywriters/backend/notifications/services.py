import requests
import json
from decouple import config
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string


BUSINESS_EMAIL = config('BUSINESS_EMAIL', default='')
WHATSAPP_API_URL = config('WHATSAPP_API_URL', default='')
WHATSAPP_API_TOKEN = config('WHATSAPP_API_TOKEN', default='')


def send_email_notification(quotation):
    """Send quotation details to business email."""
    from .models import NotificationLog

    subject = f"New Quotation Request: Q-{quotation.request_id}"
    message = _build_email_message(quotation)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=config('EMAIL_HOST_USER', default=''),
            recipient_list=[BUSINESS_EMAIL],
            fail_silently=False,
        )
        NotificationLog.objects.create(
            notification_type='email',
            recipient=BUSINESS_EMAIL,
            subject=subject,
            message=message,
            quotation=quotation,
            status='sent',
            sent_at=timezone.now(),
        )
        return True
    except Exception as e:
        NotificationLog.objects.create(
            notification_type='email',
            recipient=BUSINESS_EMAIL,
            subject=subject,
            message=message,
            quotation=quotation,
            status='failed',
            error_message=str(e),
        )
        return False


def send_whatsapp_notification(quotation):
    """Send quotation details to WhatsApp Business."""
    from .models import NotificationLog

    message = _build_whatsapp_message(quotation)

    if not WHATSAPP_API_URL or not WHATSAPP_API_TOKEN:
        NotificationLog.objects.create(
            notification_type='whatsapp',
            recipient='Business WhatsApp',
            message=message,
            quotation=quotation,
            status='failed',
            error_message='WhatsApp API not configured',
        )
        return False

    headers = {
        'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
        'Content-Type': 'application/json',
    }
    payload = {
        'messaging_product': 'whatsapp',
        'to': config('WHATSAPP_RECIPIENT_NUMBER', default=''),
        'type': 'text',
        'text': {'body': message},
    }

    try:
        resp = requests.post(WHATSAPP_API_URL, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        NotificationLog.objects.create(
            notification_type='whatsapp',
            recipient=config('WHATSAPP_RECIPIENT_NUMBER', default=''),
            message=message,
            quotation=quotation,
            status='sent',
            sent_at=timezone.now(),
        )
        return True
    except Exception as e:
        NotificationLog.objects.create(
            notification_type='whatsapp',
            recipient=config('WHATSAPP_RECIPIENT_NUMBER', default=''),
            message=message,
            quotation=quotation,
            status='failed',
            error_message=str(e),
        )
        return False


def notify_quotation(quotation):
    """Send both email and WhatsApp notifications for a quotation."""
    send_email_notification(quotation)
    send_whatsapp_notification(quotation)


def _build_email_message(q):
    currency = q.currency.code if q.currency else 'GBP'
    symbol = q.currency.symbol if q.currency else '£'
    return (
        f"NEW QUOTATION REQUEST\n"
        f"{'='*40}\n"
        f"Request ID: Q-{q.request_id}\n"
        f"Date: {q.created_at.strftime('%d %B %Y %H:%M')}\n\n"
        f"CUSTOMER DETAILS\n"
        f"{'-'*40}\n"
        f"Name: {q.customer.name}\n"
        f"Email: {q.customer.email}\n"
        f"Phone: {q.customer.phone or 'N/A'}\n"
        f"WhatsApp: {q.customer.whatsapp or 'N/A'}\n\n"
        f"SERVICE DETAILS\n"
        f"{'-'*40}\n"
        f"Service: {q.service.name if q.service else 'N/A'}\n"
        f"Academic Level: {q.academic_level.name if q.academic_level else 'N/A'}\n"
        f"Course/Subject: {q.course_subject or 'N/A'}\n"
        f"Pages: {q.pages}\n"
        f"Words: {q.words}\n"
        f"Deadline: {q.deadline.name if q.deadline else 'N/A'}\n\n"
        f"PRICING\n"
        f"{'-'*40}\n"
        f"Estimated Price: {symbol}{q.estimated_price} {currency}\n"
        f"Exchange Rate Used: {q.exchange_rate_used}\n"
        f"Pricing Season: {q.pricing_season.name if q.pricing_season else 'Normal'}\n\n"
        f"SPECIFICATIONS\n"
        f"{'-'*40}\n"
        f"{q.specifications or 'No additional specifications provided.'}\n\n"
        f"Status: {q.get_status_display()}\n"
    )


def _build_whatsapp_message(q):
    currency = q.currency.code if q.currency else 'GBP'
    symbol = q.currency.symbol if q.currency else '£'
    return (
        f"*NEW QUOTATION REQUEST*\n\n"
        f"*Request ID:* Q-{q.request_id}\n"
        f"*Date:* {q.created_at.strftime('%d %B %Y %H:%M')}\n\n"
        f"*Customer:* {q.customer.name}\n"
        f"*Email:* {q.customer.email}\n"
        f"*Phone:* {q.customer.phone or 'N/A'}\n"
        f"*WhatsApp:* {q.customer.whatsapp or 'N/A'}\n\n"
        f"*Service:* {q.service.name if q.service else 'N/A'}\n"
        f"*Level:* {q.academic_level.name if q.academic_level else 'N/A'}\n"
        f"*Subject:* {q.course_subject or 'N/A'}\n"
        f"*Pages:* {q.pages} ({q.words} words)\n"
        f"*Deadline:* {q.deadline.name if q.deadline else 'N/A'}\n\n"
        f"*Estimated Price:* {symbol}{q.estimated_price} {currency}\n\n"
        f"*Specifications:*\n{q.specifications or 'None'}\n"
    )
