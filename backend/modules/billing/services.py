from django.utils import timezone
from .models import Plan, Subscription

def effective_entitlement(user):
    now = timezone.now()
    active = Subscription.objects.filter(owner=user, status=Subscription.ACTIVE, verified_at__isnull=False,
        starts_at__lte=now, expires_at__gt=now, plan__is_active=True, plan__code=Plan.PREMIUM).select_related("plan").order_by("-expires_at").first()
    plan = active.plan if active else Plan.objects.get(code=Plan.FREE, is_active=True)
    return {"plan": plan, "subscription": active}


def payment_availability(plan=None):
    from django.conf import settings
    if not getattr(settings, "PAYMENTS_ENABLED", False):
        reason = "payments_disabled"
    elif not getattr(settings, "PAYMENT_MERCHANT_APPROVED", False):
        reason = "merchant_not_approved"
    elif not getattr(settings, "PAYMENT_PROVIDER", "") or not getattr(settings, "PAYMENT_ADAPTER_READY", False):
        reason = "provider_not_configured"
    elif not getattr(settings, "PAYMENT_API_KEY", "") or not getattr(settings, "PAYMENT_WEBHOOK_SECRET", ""):
        reason = "credentials_missing"
    elif plan and (not plan.purchase_enabled or plan.price_afn is None or not plan.term_days):
        reason = "plan_not_available_for_purchase"
    else:
        reason = "available"
    return {"checkout_available": reason == "available", "reason": reason}
