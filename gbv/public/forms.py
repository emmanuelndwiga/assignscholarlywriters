from django import forms
from django.utils import timezone
from cases.models import CaseReport, TRACKING_CODE_ALPHABET, TRACKING_CODE_LENGTH
import re

ALLOWED_ATTACHMENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB


class CaseReportForm(forms.ModelForm):
    class Meta:
        model = CaseReport
        fields = [
            "category", "description",
            "date_of_incident", "approximate_time",
            "platform", "platform_other",
            "location_context", "relationship_to_perpetrator",
            "perpetrator_name", "perpetrator_username",
            "perpetrator_profile_url", "perpetrator_contact",
            "perpetrator_additional_info",
            "contact_method", "contact_value",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Describe what happened, in your own words."}),
            "date_of_incident": forms.DateInput(attrs={"type": "date"}),
            "approximate_time": forms.TextInput(attrs={"placeholder": "e.g. Evening, around 8pm, not sure"}),
            "location_context": forms.TextInput(attrs={"placeholder": "e.g. Nairobi CBD, a university WhatsApp group"}),
            "perpetrator_additional_info": forms.Textarea(attrs={"rows": 3}),
            "contact_value": forms.TextInput(attrs={"placeholder": "Email address or phone number"}),
        }

    def clean_date_of_incident(self):
        date = self.cleaned_data.get("date_of_incident")
        if date and date > timezone.now().date():
            raise forms.ValidationError("Incident date can't be in the future.")
        return date

    def clean(self):
        cleaned = super().clean()
        method = cleaned.get("contact_method")
        value = cleaned.get("contact_value")
        if method and method != CaseReport.ContactMethod.NONE and not value:
            raise forms.ValidationError("Please provide contact details, or choose 'No contact'.")
        return cleaned



class TrackingForm(forms.Form):
    reference_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            "placeholder": "GBV-2026-000000",
            "autocapitalize": "characters",
        }),
    )
    tracking_code = forms.CharField(
        max_length=TRACKING_CODE_LENGTH,
        widget=forms.TextInput(attrs={
            "placeholder": "XXXX-XXXX",
            "maxlength": TRACKING_CODE_LENGTH + 1,  # room for the dash while typing
            "autocapitalize": "characters",
            "autocomplete": "off",
            "class": "tracking-code-input",
        }),
    )

    def clean_reference_number(self):
        return self.cleaned_data["reference_number"].strip().upper()

    def clean_tracking_code(self):
        # strip whitespace/dashes the victim may have typed and normalize case,
        # since the stored code is uppercase from TRACKING_CODE_ALPHABET
        raw = self.cleaned_data["tracking_code"]
        cleaned = re.sub(r"[\s-]", "", raw).upper()
        if len(cleaned) != TRACKING_CODE_LENGTH:
            raise forms.ValidationError(f"Tracking code should be {TRACKING_CODE_LENGTH} characters.")
        if any(ch not in TRACKING_CODE_ALPHABET for ch in cleaned):
            raise forms.ValidationError("Tracking code contains an invalid character.")
        return cleaned

class ReplyForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Write a message to your case handler..."}))