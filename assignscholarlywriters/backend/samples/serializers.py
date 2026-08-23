from rest_framework import serializers
from .models import Sample


class SampleSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    filename = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()

    class Meta:
        model = Sample
        fields = [
            'id', 'title', 'subject', 'level', 'pages', 'format',
            'description', 'category', 'file_url', 'filename',
            'file_extension', 'order', 'is_active', 'created_at',
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return ''

    def get_filename(self, obj):
        return obj.filename

    def get_file_extension(self, obj):
        return obj.file_extension
