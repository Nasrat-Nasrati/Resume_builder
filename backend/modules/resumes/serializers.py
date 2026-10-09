import json
from rest_framework import serializers
from .models import CVDocument
from .services import ALLOWED_SECTIONS
from modules.exports.templates import TEMPLATE_CATALOG, validate_design_options

class ResumeDocumentSerializer(serializers.ModelSerializer):
    has_photo = serializers.SerializerMethodField()
    class Meta:
        model = CVDocument
        fields = ["id", "title", "cv_type", "lifecycle_state", "output_language", "schema_version", "template_version", "template_key", "design_options", "revision", "builder_step", "last_completed_step", "selected_sections", "snapshot", "has_photo", "created_at", "updated_at"]
        read_only_fields = fields
    def get_has_photo(self, obj):
        return hasattr(obj, "photo")

class CreateBlankResumeSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=160, default="Untitled CV")
    output_language = serializers.ChoiceField(choices=["en", "fa", "ps"], default="en")
    cv_type = serializers.ChoiceField(choices=CVDocument.CV_TYPES, default="general")

class CreateResumeFromProfileSerializer(CreateBlankResumeSerializer):
    selected_sections = serializers.ListField(child=serializers.ChoiceField(choices=sorted(ALLOWED_SECTIONS)), allow_empty=False, max_length=len(ALLOWED_SECTIONS))
    def validate_selected_sections(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate sections are not allowed.")
        return value

class RevisionSerializer(serializers.Serializer):
    expected_revision = serializers.IntegerField(min_value=1)
    request_id = serializers.UUIDField(required=False)

class MetadataSerializer(RevisionSerializer):
    title = serializers.CharField(max_length=160, required=False)
    output_language = serializers.ChoiceField(choices=["en", "fa", "ps"], required=False)
    cv_type = serializers.ChoiceField(choices=CVDocument.CV_TYPES, required=False)
    builder_step = serializers.IntegerField(min_value=1, max_value=4, required=False)
    template_key = serializers.ChoiceField(choices=sorted(TEMPLATE_CATALOG), required=False)
    design_options = serializers.DictField(required=False)
    def validate_design_options(self, value):
        template_key = self.initial_data.get("template_key") or (self.instance.template_key if self.instance else "public-service-v1")
        try:
            return validate_design_options(template_key, value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

class WizardStepSerializer(RevisionSerializer):
    data = serializers.DictField()
    complete = serializers.BooleanField(default=False)
    def validate_data(self, value):
        if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > 100_000:
            raise serializers.ValidationError("Step data is too large. Upload photos separately.")
        return value
