import sys
from django.core.management.base import BaseCommand
from django.core.mail import EmailMessage
from django.conf import settings


class Command(BaseCommand):
    help = 'Send a test email to verify SMTP configuration works.'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, default='', help='Recipient email (defaults to BUSINESS_EMAIL)')

    def handle(self, *args, **options):
        to_email = options['to'] or getattr(settings, 'BUSINESS_EMAIL', '')
        if not to_email:
            self.stderr.write(self.style.ERROR('No recipient. Set BUSINESS_EMAIL in .env or use --to'))
            return

        from_email = getattr(settings, 'EMAIL_HOST_USER', '')
        if not from_email:
            self.stderr.write(self.style.ERROR('EMAIL_HOST_USER not set in .env'))
            return

        self.stdout.write(f'Sending test email from {from_email} to {to_email}...')
        self.stdout.write(f'  SMTP host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}')
        self.stdout.write(f'  TLS: {settings.EMAIL_USE_TLS}')

        try:
            msg = EmailMessage(
                subject='ScholarlyWriters - Email Test',
                body=(
                    'This is a test email from your ScholarlyWriters Django backend.\n\n'
                    'If you received this, your SMTP configuration is working correctly.\n\n'
                    'Contact form submissions and quotation notifications will be sent to this address.'
                ),
                from_email=from_email,
                to=[to_email],
            )
            msg.send(fail_silently=False)
            self.stdout.write(self.style.SUCCESS(f'Success! Test email sent to {to_email}'))
            self.stdout.write('Check your inbox (and spam folder).')
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Failed to send email: {e}'))
            self.stderr.write('')
            self.stderr.write('Common fixes:')
            self.stderr.write('  1. Make sure you are using a Gmail APP PASSWORD (not your regular password)')
            self.stderr.write('     → Go to https://myaccount.google.com/apppasswords')
            self.stderr.write('  2. Make sure 2-Step Verification is enabled on your Google account')
            self.stderr.write('  3. Check that EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are set in .env')
