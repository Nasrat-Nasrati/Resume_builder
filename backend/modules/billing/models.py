from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

class Plan(models.Model):
    FREE = "free"
    PREMIUM = "premium"
    code = models.SlugField(max_length=24, unique=True)
    name = models.CharField(max_length=80)
    rolling_window_hours = models.PositiveSmallIntegerField(default=24)
    export_limit = models.PositiveSmallIntegerField()
    allowed_formats = models.JSONField(default=list)
    allowed_templates = models.JSONField(default=list)
    watermark_exports = models.BooleanField(default=True)
    purchase_enabled = models.BooleanField(default=False)
    price_afn = models.PositiveIntegerField(null=True, blank=True)
    term_days = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["export_limit", "code"]
        constraints = [models.CheckConstraint(condition=Q(export_limit__gt=0), name="plan_export_limit_positive")]

    def clean(self):
        if not self.allowed_formats or set(self.allowed_formats) - {"pdf", "docx"}:
            raise ValidationError({"allowed_formats": "Choose one or more supported formats."})
        if not self.allowed_templates:
            raise ValidationError({"allowed_templates": "Choose at least one template."})
        if self.purchase_enabled and (self.price_afn is None or not self.term_days):
            raise ValidationError("A purchasable plan requires an approved price and term.")

    def __str__(self):
        return self.name

class Subscription(models.Model):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=12, choices=[(ACTIVE, "Active"), (EXPIRED, "Expired"), (REVOKED, "Revoked")], default=ACTIVE)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    provider_reference = models.CharField(max_length=160, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-expires_at"]
        indexes = [models.Index(fields=["owner", "status", "expires_at"], name="subscription_owner_active_idx")]
