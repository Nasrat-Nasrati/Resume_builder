import re
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User


def normalize_afghan_phone(value: str) -> str:
    compact = re.sub(r"[\s()\-]", "", value)
    if compact.startswith("00"):
        compact = "+" + compact[2:]
    if compact.startswith("07"):
        compact = "+93" + compact[1:]
    elif compact.startswith("7") and len(compact) == 9:
        compact = "+93" + compact
    if not re.fullmatch(r"\+937\d{8}", compact):
        raise serializers.ValidationError("Enter a valid Afghan mobile number, such as +93701234567.")
    return compact


class RegistrationSerializer(serializers.Serializer):
    full_name = serializers.CharField(min_length=2, max_length=150, trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=32)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_phone(self, value):
        return normalize_afghan_phone(value)

    def create(self, validated_data):
        names = validated_data.pop("full_name").split(maxsplit=1)
        return User.objects.create_user(
            email=validated_data["email"], password=None,
            first_name=names[0], last_name=names[1] if len(names) > 1 else "",
            phone=validated_data["phone"], is_active=False,
        )


class ActivateAccountSerializer(serializers.Serializer):
    token = serializers.CharField(trim_whitespace=False, write_only=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})

    def validate_password(self, value):
        try:
            validate_password(value, user=self.context.get("user"))
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    def validate_email(self, value):
        return value.strip().lower()

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField(trim_whitespace=False)
    password = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})
    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value

class AccountSettingsSerializer(serializers.Serializer):
    full_name = serializers.CharField(min_length=2, max_length=150, trim_whitespace=True)
    phone = serializers.CharField(max_length=32, allow_blank=True, required=False)
    preferred_language = serializers.ChoiceField(choices=["en", "fa", "ps"])
    new_email = serializers.EmailField(max_length=254, required=False, allow_blank=True)
    def validate_phone(self, value):
        return normalize_afghan_phone(value) if value.strip() else ""
    def validate_new_email(self, value):
        return value.strip().lower()
