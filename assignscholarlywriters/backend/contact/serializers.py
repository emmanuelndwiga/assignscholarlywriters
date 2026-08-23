from rest_framework import serializers
from .models import ContactMessage, ContactAttachment


class ContactAttachmentSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(source='original_filename', read_only=True)

    class Meta:
        model = ContactAttachment
        fields = ['id', 'filename', 'uploaded_at']


class ContactMessageSerializer(serializers.ModelSerializer):
    attachments = ContactAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'service', 'message', 'attachments', 'created_at']
        read_only_fields = ['created_at']
