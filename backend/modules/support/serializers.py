from rest_framework import serializers
from .models import ContactSubmission


class ContactSubmissionSerializer(serializers.Serializer):
    sender_email = serializers.EmailField(max_length=254)
    category = serializers.ChoiceField(choices=["general", "account", "technical", "billing", "other"])
    subject = serializers.CharField(max_length=160, trim_whitespace=True)
    message = serializers.CharField(max_length=5000, trim_whitespace=True)
    website = serializers.CharField(max_length=200, allow_blank=True, required=False, write_only=True, default="")

    def validate_subject(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Enter a more descriptive subject.")
        return value.strip()

    def validate_message(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Please include a little more detail.")
        return value.strip()


class ContactSubmissionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ["id", "delivery_status", "created_at"]
