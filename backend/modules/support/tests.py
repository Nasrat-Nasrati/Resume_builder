from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import ContactSubmission, PublicContent


class PublicSupportTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_public_content_includes_draft_status_and_selected_language(self):
        PublicContent.objects.create(key="privacy", version="test", status="draft", title_by_language={"en":"Privacy draft","fa":"حریم خصوصی"}, body_by_language={"en":["Draft text"],"fa":["متن"]})
        response = self.client.get("/api/v1/support/content/privacy/?lang=fa")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["title"], "حریم خصوصی")
        self.assertIn("public", response["Cache-Control"])

    @override_settings(SUPPORT_EMAIL="")
    def test_contact_is_saved_without_claiming_delivery_when_support_is_unconfigured(self):
        response = self.client.post("/api/v1/support/contact/", {"sender_email":"person@example.com", "category":"general", "subject":"A question", "message":"I need help with a CV."}, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["delivery_status"], "unavailable")
        self.assertEqual(ContactSubmission.objects.count(), 1)
        self.assertNotIn("message", response.data)

    def test_honeypot_returns_generic_response_without_persisting(self):
        response = self.client.post("/api/v1/support/contact/", {"sender_email":"bot@example.com", "category":"other", "subject":"Spam message", "message":"A long enough spam message.", "website":"https://spam.invalid"}, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(ContactSubmission.objects.count(), 0)

    def test_contact_rate_limit_caps_repeated_submissions(self):
        payload = {"sender_email":"person@example.com", "category":"general", "subject":"A question", "message":"I need help with a CV."}
        statuses = [self.client.post("/api/v1/support/contact/", payload, format="json").status_code for _ in range(6)]
        self.assertEqual(statuses[:5], [202] * 5)
        self.assertEqual(statuses[5], 429)
        self.assertEqual(ContactSubmission.objects.count(), 5)

    @override_settings(SUPPORT_EMAIL="support@example.com")
    def test_broker_failure_keeps_submission_and_marks_delivery_failed(self):
        from unittest.mock import patch
        from .views import send_contact_notification
        with patch.object(send_contact_notification, "delay", side_effect=ConnectionError("offline")):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post("/api/v1/support/contact/", {"sender_email":"person@example.com", "category":"general", "subject":"A question", "message":"I need help with a CV."}, format="json")
        self.assertEqual(response.status_code, 202)
        submission = ContactSubmission.objects.get()
        self.assertEqual(submission.delivery_status, ContactSubmission.FAILED)
        self.assertEqual(submission.message, "I need help with a CV.")
