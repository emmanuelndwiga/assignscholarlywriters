import os
from django.db import models


class Sample(models.Model):
    CATEGORY_CHOICES = [
        ('essay', 'Essay'),
        ('research', 'Research Paper'),
        ('dissertation', 'Dissertation'),
        ('case-study', 'Case Study'),
    ]

    title = models.CharField(max_length=300)
    subject = models.CharField(max_length=150)
    level = models.CharField(max_length=100)
    pages = models.PositiveIntegerField()
    format = models.CharField(max_length=50, help_text='Citation format, e.g. APA, MLA, Harvard')
    file = models.FileField(upload_to='samples/')
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name_plural = 'Samples'
        indexes = [
            models.Index(fields=['category', 'is_active'], name='sample_cat_active_idx'),
        ]

    def __str__(self):
        return self.title

    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        return ''

    @property
    def file_url(self):
        if self.file:
            return self.file.url
        return ''

    @property
    def file_extension(self):
        if self.file:
            name = os.path.basename(self.file.name)
            _, ext = os.path.splitext(name)
            return ext.lstrip('.').lower()
        return ''
