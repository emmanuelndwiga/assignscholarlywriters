# cases/models.py
import secrets
import string

from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


def generate_reference():
    year = timezone.now().year
    suffix = "".join(secrets.choice(string.digits) for _ in range(6))
    return f"GBV-{year}-{suffix}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CaseReport(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        ESCALATED = "escalated", "Escalated"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"
        TIKTOK = "tiktok", "TikTok"
        WHATSAPP = "whatsapp", "WhatsApp"
        X_TWITTER = "x_twitter", "X (Twitter)"
        TELEGRAM = "telegram", "Telegram"
        SMS_CALL = "sms_call", "SMS / Phone Call"
        EMAIL = "email", "Email"
        DATING_APP = "dating_app", "Dating App"
        OTHER = "other", "Other"
        NOT_APPLICABLE = "n/a", "Not applicable"

    class Relationship(models.TextChoices):
        STRANGER = "stranger", "Stranger"
        ACQUAINTANCE = "acquaintance", "Acquaintance"
        FRIEND = "friend", "Friend"
        FAMILY = "family", "Family member"
        INTIMATE_PARTNER = "partner", "Current/former intimate partner"
        COLLEAGUE = "colleague", "Colleague/Classmate"
        UNKNOWN = "unknown", "Unknown/Prefer not to say"
        OTHER = "other", "Other"

    class ContactMethod(models.TextChoices):
        NONE = "none", "No contact / don't notify"
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone (SMS)"

    # -- identifiers --
    reference_number = models.CharField(max_length=20, unique=True, default=generate_reference, editable=False)
    tracking_code_hash = models.CharField(max_length=128)

    # -- classification --
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="cases")
    description = models.TextField()

    # -- incident context --
    date_of_incident = models.DateField(null=True, blank=True)
    approximate_time = models.CharField(
        max_length=50, blank=True,
        help_text="e.g. 'Morning', 'Around 8pm', 'Not sure'",
    )
    platform = models.CharField(max_length=20, choices=Platform.choices, blank=True)
    platform_other = models.CharField(max_length=100, blank=True)
    location_context = models.CharField(
        max_length=255, blank=True,
        help_text="Physical location or online context",
    )
    relationship_to_perpetrator = models.CharField(max_length=20, choices=Relationship.choices, blank=True)

    # -- perpetrator info (all optional) --
    perpetrator_name = models.CharField(max_length=255, blank=True)
    perpetrator_username = models.CharField(max_length=255, blank=True)
    perpetrator_profile_url = models.URLField(max_length=500, blank=True)
    perpetrator_contact = models.CharField(max_length=255, blank=True)
    perpetrator_additional_info = models.TextField(blank=True)

    # -- optional contact for notifications --
    contact_method = models.CharField(max_length=10, choices=ContactMethod.choices, default=ContactMethod.NONE)
    contact_value = models.CharField(max_length=255, blank=True)

    # -- case handling --
    assigned_handler = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="assigned_cases", limit_choices_to={"role": "case_handler"},
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.reference_number

    def set_tracking_code(self, raw_code: str):
        self.tracking_code_hash = make_password(raw_code)

    def check_tracking_code(self, raw_code: str) -> bool:
        return check_password(raw_code, self.tracking_code_hash)


class Attachment(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename


class CaseUpdate(models.Model):
    class AuthorType(models.TextChoices):
        HANDLER = "handler", "Case Handler"
        VICTIM = "victim", "Victim"

    class Visibility(models.TextChoices):
        VICTIM = "victim", "Visible to victim"
        INTERNAL = "internal", "Internal note only"

    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name="updates")
    author_type = models.CharField(max_length=10, choices=AuthorType.choices)
    author_user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField()
    visibility = models.CharField(max_length=10, choices=Visibility.choices, default=Visibility.VICTIM)
    is_read_by_victim = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.case.reference_number} - {self.get_author_type_display()} - {self.created_at:%Y-%m-%d %H:%M}"


class CaseAuditLog(models.Model):
    case = models.ForeignKey(CaseReport, on_delete=models.CASCADE, related_name="audit_log")
    actor = models.ForeignKey("accounts.User", null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.case.reference_number} - {self.action} - {self.timestamp:%Y-%m-%d %H:%M}"