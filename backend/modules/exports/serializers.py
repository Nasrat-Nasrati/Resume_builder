from rest_framework import serializers
from .models import ExportJob
from .templates import TEMPLATE_CATALOG

class CreateExportSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    template_key = serializers.ChoiceField(choices=sorted(TEMPLATE_CATALOG), default="public-service-v1")
    format = serializers.ChoiceField(choices=[ExportJob.PDF, ExportJob.DOCX], default=ExportJob.PDF)
    purpose = serializers.ChoiceField(choices=[ExportJob.PREVIEW, ExportJob.EXPORT], default=ExportJob.EXPORT)
    idempotency_key = serializers.UUIDField()

class ExportJobSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    class Meta:
        model = ExportJob
        fields = ["id", "document", "document_revision", "content_hash", "format", "purpose", "status", "template_key", "failure_code", "download_url", "preview_url", "created_at", "updated_at"]
        read_only_fields = fields
    def get_download_url(self, obj):
        if obj.purpose == ExportJob.EXPORT and obj.status == ExportJob.SUCCEEDED and obj.artifact:
            return f"/api/v1/exports/{obj.pk}/download/"
        return None
    def get_preview_url(self, obj):
        if obj.purpose == ExportJob.PREVIEW and obj.status == ExportJob.SUCCEEDED and obj.artifact:
            return f"/api/v1/exports/{obj.pk}/preview/"
        return None
