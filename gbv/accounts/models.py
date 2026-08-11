from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        CASE_HANDLER = "case_handler", "Case Handler"
        SUPERVISOR = "supervisor", "Supervisor/Escalator"

    role = models.CharField(max_length=20, choices=Role.choices)
    phone_number = models.CharField(max_length=20, blank=True)

    class Meta:
        permissions = [
            ("escalate_case", "Can escalate a case"),
            ("view_all_cases", "Can view all cases, not just assigned ones"),
        ]