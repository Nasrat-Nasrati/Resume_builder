from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Plan


class PaymentReadinessTests(TestCase):
    def test_checkout_is_closed_without_merchant_provider_and_approved_price(self):
        response = APIClient().get("/api/v1/billing/readiness/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["checkout_available"])
        self.assertIsNone(response.data["price_afn"])
        self.assertFalse(response.data["purchase_enabled"])
        self.assertNotIn("api_key", response.data)
        premium = APIClient().get("/api/v1/billing/plans/").data["results"]
        plan = next(plan for plan in premium if plan["code"] == "premium")
        self.assertFalse(plan["checkout_available"])
        self.assertIsNone(plan["price_afn"])
        self.assertFalse(plan["purchase_enabled"])

    @override_settings(PAYMENTS_ENABLED=True, PAYMENT_MERCHANT_APPROVED=True, PAYMENT_PROVIDER="selected-provider",
        PAYMENT_API_KEY="server-secret", PAYMENT_WEBHOOK_SECRET="server-webhook-secret", PAYMENT_ADAPTER_READY=False)
    def test_configuration_does_not_open_checkout_without_implemented_provider_adapter(self):
        Plan.objects.filter(code="premium").update(purchase_enabled=True, price_afn=1000, term_days=30)
        response = APIClient().get("/api/v1/billing/readiness/")
        self.assertFalse(response.data["checkout_available"])
        self.assertEqual(response.data["reason"], "provider_not_configured")
        self.assertNotIn("server-secret", str(response.data))
        self.assertNotIn("server-webhook-secret", str(response.data))
