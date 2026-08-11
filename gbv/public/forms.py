# public/forms.py
from django import forms
from django.core.exceptions import ValidationError

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB

class AttachmentForm(forms.Form):
    file = forms.FileField(required=False)

    def clean_file(self):
        f = self.cleaned_data.get("file")
        if f:
            if f.content_type not in ALLOWED_TYPES:
                raise ValidationError("Unsupported file type.")
            if f.size > MAX_SIZE:
                raise ValidationError("File too large (max 10MB).")
        return f