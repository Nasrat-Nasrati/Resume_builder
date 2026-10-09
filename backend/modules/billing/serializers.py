from rest_framework import serializers
from .models import Plan
from .services import effective_entitlement

class PlanSerializer(serializers.ModelSerializer):
    currency = serializers.SerializerMethodField()
    checkout_available = serializers.SerializerMethodField()
    class Meta:
        model = Plan
        fields = ["code", "name", "rolling_window_hours", "export_limit", "allowed_formats", "allowed_templates", "watermark_exports", "purchase_enabled", "price_afn", "currency", "term_days", "checkout_available"]
    def get_currency(self, obj):
        return "AFN" if obj.price_afn is not None else None
    def get_checkout_available(self, obj):
        from .services import payment_availability
        return payment_availability(obj)["checkout_available"]

class EntitlementSerializer(serializers.Serializer):
    plan = PlanSerializer()
    status = serializers.CharField()
    starts_at = serializers.DateTimeField(allow_null=True)
    expires_at = serializers.DateTimeField(allow_null=True)

    @classmethod
    def to_data(cls, user):
        resolved = effective_entitlement(user)
        subscription = resolved["subscription"]
        return {"plan": resolved["plan"], "status": subscription.status if subscription else "free",
            "starts_at": subscription.starts_at if subscription else None, "expires_at": subscription.expires_at if subscription else None}
