from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Plan
from .serializers import EntitlementSerializer, PlanSerializer
from .services import payment_availability

class PlanListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PlanSerializer
    queryset = Plan.objects.filter(is_active=True)

class MyEntitlementView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(EntitlementSerializer.to_data(request.user))


class PaymentReadinessView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request):
        plan = Plan.objects.filter(code=Plan.PREMIUM, is_active=True).first()
        return Response({**payment_availability(plan), "currency": "AFN", "price_afn": plan.price_afn if plan else None,
            "term_days": plan.term_days if plan else None, "purchase_enabled": bool(plan and plan.purchase_enabled)})
