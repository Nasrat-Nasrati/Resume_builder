from datetime import datetime, time, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import F, Sum
from django.utils import timezone
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from modules.accounts.models import User
from modules.resumes.models import ExportCharge
from .models import PageViewDaily

KABUL = ZoneInfo("Asia/Kabul")
PUBLIC_PATHS = {"/", "/templates", "/pricing", "/stats", "/contact", "/faq", "/privacy", "/terms"}
BOT_MARKERS = ("bot", "crawler", "spider", "headless", "preview")


class PageViewThrottle(AnonRateThrottle):
    scope = "page_view"


class PageViewSerializer(serializers.Serializer):
    path = serializers.ChoiceField(choices=sorted(PUBLIC_PATHS))


class PublicStatsView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request):
        key = "kabulcv-public-stats-v1"
        data = cache.get(key)
        if data is None:
            local_now = timezone.now().astimezone(KABUL)
            local_start = datetime.combine(local_now.date(), time.min, tzinfo=KABUL)
            local_end = local_start + timedelta(days=1)
            start_utc, end_utc = local_start.astimezone(dt_timezone.utc), local_end.astimezone(dt_timezone.utc)
            data = {
                "activated_accounts": User.objects.filter(activated_at__isnull=False).count(),
                "successful_cv_exports": ExportCharge.objects.count(),
                "activated_accounts_today": User.objects.filter(activated_at__gte=start_utc, activated_at__lt=end_utc).count(),
                "successful_cv_exports_today": ExportCharge.objects.filter(charged_at__gte=start_utc, charged_at__lt=end_utc).count(),
                "page_views_today": PageViewDaily.objects.filter(page_date=local_now.date()).aggregate(total=Sum("view_count"))["total"] or 0,
                "metric_timezone": "Asia/Kabul",
                "definitions": {"activated_accounts": "Accounts that completed email activation.",
                    "successful_cv_exports": "Distinct CVs with a first successful export; repeat downloads do not add counts.",
                    "page_views_today": "Public page entries, not unique people."},
            }
            cache.set(key, data, 60)
        response = Response(data)
        response["Cache-Control"] = "public, max-age=60, stale-while-revalidate=30"
        return response


class PublicPageViewView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [PageViewThrottle]
    serializer_class = PageViewSerializer
    def post(self, request):
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        if any(marker in user_agent for marker in BOT_MARKERS):
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        path = serializer.validated_data["path"]
        page_date = timezone.now().astimezone(KABUL).date()
        PageViewDaily.objects.filter(page_date__lt=page_date - timedelta(days=90)).delete()
        updated = PageViewDaily.objects.filter(page_date=page_date, path=path).update(view_count=F("view_count") + 1)
        if not updated:
            try:
                PageViewDaily.objects.create(page_date=page_date, path=path, view_count=1)
            except IntegrityError:
                # A simultaneous first view created the unique daily row.
                PageViewDaily.objects.filter(page_date=page_date, path=path).update(view_count=F("view_count") + 1)
        cache.delete("kabulcv-public-stats-v1")
        response = Response(status=status.HTTP_204_NO_CONTENT)
        response["Cache-Control"] = "no-store"
        return response
