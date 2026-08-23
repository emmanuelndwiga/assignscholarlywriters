import os
from django.db import models


class ContactMessage(models.Model):
    SERVICE_CHOICES = [
        ('essay', 'Essay Writing'),
        ('research', 'Research Paper'),
        ('dissertation', 'Dissertation'),
        ('editing', 'Editing & Proofreading'),
        ('admission', 'Admission Essay'),
        ('case-study', 'Case Study'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    email = models.EmailField()
    service = models.CharField(max_length=50, choices=SERVICE_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.email}) - {self.service}"


class ContactAttachment(models.Model):
    contact = models.ForeignKey(ContactMessage, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='contact/%Y/%m/')
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_filename

    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        return ''
