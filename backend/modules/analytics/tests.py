from datetime import timedelta
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import PageViewDaily


class PublicAnalyticsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def test_stats_return_real_zero_values_and_definitions(self):
        response = self.client.get("/api/v1/analytics/stats/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["activated_accounts"], 0)
        self.assertEqual(response.data["successful_cv_exports"], 0)
        self.assertEqual(response.data["page_views_today"], 0)
        self.assertEqual(response.data["metric_timezone"], "Asia/Kabul")
        self.assertIn("definitions", response.data)

    def test_page_views_aggregate_by_kabul_date_without_identity(self):
        path = "/faq"
        response = self.client.post("/api/v1/analytics/page-views/", {"path": path}, format="json")
        self.assertEqual(response.status_code, 204)
        row = PageViewDaily.objects.get(path=path)
        self.assertEqual(row.page_date, timezone.now().astimezone(ZoneInfo("Asia/Kabul")).date())
        self.assertEqual(row.view_count, 1)
        self.client.post("/api/v1/analytics/page-views/", {"path": path}, format="json")
        row.refresh_from_db()
        self.assertEqual(row.view_count, 2)
        self.assertEqual({f.name for f in PageViewDaily._meta.fields}, {"id", "page_date", "path", "view_count"})

    def test_page_view_rejects_non_public_paths_and_ignores_bots(self):
        invalid = self.client.post("/api/v1/analytics/page-views/", {"path": "/dashboard"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        bot_client = APIClient(HTTP_USER_AGENT="ExampleBot/1.0")
        response = bot_client.post("/api/v1/analytics/page-views/", {"path": "/"}, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(PageViewDaily.objects.filter(path="/").exists())

    def test_old_daily_rows_are_pruned_after_90_days(self):
        old_date = timezone.now().astimezone(ZoneInfo("Asia/Kabul")).date() - timedelta(days=91)
        PageViewDaily.objects.create(page_date=old_date, path="/", view_count=12)
        self.client.post("/api/v1/analytics/page-views/", {"path": "/faq"}, format="json")
        self.assertFalse(PageViewDaily.objects.filter(page_date=old_date).exists())
