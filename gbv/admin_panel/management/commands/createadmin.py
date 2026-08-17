from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create a default admin (supervisor) user for testing"

    def handle(self, *args, **options):
        username = "admin"
        email = "admin@safereport.com"
        password = "admin1234"

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists."))
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role="supervisor",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
        )
        self.stdout.write(self.style.SUCCESS(
            f"Created user: {username} / {password} (supervisor)"
        ))
