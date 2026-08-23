import logging
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from .models import ContactMessage, ContactAttachment
from .serializers import ContactMessageSerializer

logger = logging.getLogger('contact')

ALLOWED_UPLOAD_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.rtf', '.xlsx', '.pptx', '.zip', '.png', '.jpg', '.jpeg', '.gif'}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
BUSINESS_EMAIL = getattr(settings, 'BUSINESS_EMAIL', '') or 'scholarlywriters9@gmail.com'


class ContactCreateThrottle(SimpleRateThrottle):
    scope = 'contact_create'


class CreateContactView(generics.GenericAPIView):
    """
    Receive contact form submission with optional file attachments.
    Saves to DB and sends an email with attachments to the business email.
    """
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ContactCreateThrottle]

    @transaction.atomic
    def post(self, request):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        service = request.data.get('service', '').strip()
        message_text = request.data.get('message', '').strip()

        if not all([name, email, message_text]):
            return Response(
                {'error': 'Name, email, and message are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        contact = ContactMessage.objects.create(
            name=name,
            email=email,
            service=service or 'other',
            message=message_text,
        )

        # Handle file uploads
        files = request.FILES.getlist('attachments')
        saved_files = []
        for f in files:
            ext = ('.' + f.name.rsplit('.', 1)[-1].lower()) if '.' in f.name else ''
            if ext not in ALLOWED_UPLOAD_EXTENSIONS:
                return Response(
                    {'error': f'File type not allowed: {ext}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if f.size > MAX_UPLOAD_SIZE:
                return Response(
                    {'error': f'File too large: {f.name} (max 10MB)'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            attachment = ContactAttachment.objects.create(
                contact=contact,
                file=f,
                original_filename=f.name,
            )
            saved_files.append(attachment)

        logger.info('Contact form submitted: %s <%s> [%s]', name, email, service)

        # Send email with attachments
        try:
            subject = f'New Contact: {name} - {contact.get_service_display()}'
            body = (
                f'NEW CONTACT FORM SUBMISSION\n'
                f'{"=" * 40}\n\n'
                f'Name: {name}\n'
                f'Email: {email}\n'
                f'Service: {contact.get_service_display()}\n\n'
                f'Message:\n{message_text}\n'
            )
            if saved_files:
                body += f'\nAttachments: {", ".join(a.original_filename for a in saved_files)}\n'

            email_msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.EMAIL_HOST_USER or email,
                to=[BUSINESS_EMAIL],
                reply_to=[email],
            )

            for attachment in saved_files:
                attachment.file.open('rb')
                email_msg.attach(
                    attachment.original_filename,
                    attachment.file.read(),
                )
                attachment.file.close()

            email_msg.send(fail_silently=False)
            logger.info('Contact email sent for %s', name)
        except Exception:
            logger.exception('Failed to send contact email for %s', name)

        return Response({
            'success': True,
            'message': 'Your message has been sent. We will get back to you shortly.',
            'id': contact.id,
        }, status=status.HTTP_201_CREATED)
