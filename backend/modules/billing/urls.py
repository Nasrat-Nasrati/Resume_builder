from django.urls import path
from .views import MyEntitlementView, PlanListView, PaymentReadinessView

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan-list"),
    path("me/", MyEntitlementView.as_view(), name="my-entitlement"),
    path("readiness/", PaymentReadinessView.as_view(), name="payment-readiness"),
]
