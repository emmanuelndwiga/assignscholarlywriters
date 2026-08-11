# accounts/models.py
import secrets
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


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


def generate_invite_token():
    return secrets.token_urlsafe(32)


def default_expiry():
    return timezone.now() + timedelta(days=3)


class StaffInvitation(models.Model):
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=User.Role.choices, default=User.Role.CASE_HANDLER)
    token = models.CharField(max_length=64, unique=True, default=generate_invite_token, editable=False)

    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="invitations_sent"
    )
    expires_at = models.DateTimeField(default=default_expiry)
    accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def is_valid(self):
        return self.accepted_at is None and timezone.now() < self.expires_at

    def __str__(self):
        return f"Invite for {self.email} ({self.get_role_display()})"