from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from modules.accounts.tokens import make_email_change_token

User = get_user_model()

class RecoveryAndSettingsTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email="person@example.com", password="T9!Violet-Cedar-421", is_active=True, first_name="Person")

    @patch("modules.accounts.views.send_password_reset_email.delay")
    def test_reset_request_is_generic_and_reset_token_is_single_use(self, send_email):
        known = self.client.post("/api/v1/accounts/password/reset/", {"email": self.user.email}, format="json")
        unknown = self.client.post("/api/v1/accounts/password/reset/", {"email": "unknown@example.com"}, format="json")
        self.assertEqual(known.status_code, 202)
        self.assertEqual(unknown.status_code, 202)
        self.assertEqual(known.data["detail"], unknown.data["detail"])
        send_email.assert_called_once_with(str(self.user.pk))
        refresh = RefreshToken.for_user(self.user)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        from django.contrib.auth.tokens import default_token_generator
        token = default_token_generator.make_token(self.user)
        payload = {"uid": uid, "token": token, "password": "New9!Violet-Cedar-752"}
        response = self.client.post("/api/v1/accounts/password/reset/confirm/", payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertTrue(BlacklistedToken.objects.filter(token__user=self.user).exists())
        repeated = self.client.post("/api/v1/accounts/password/reset/confirm/", payload, format="json")
        self.assertEqual(repeated.status_code, 400)

    @patch("modules.accounts.views.send_email_change_verification.delay")
    @patch("modules.accounts.views.send_mail")
    def test_email_change_waits_for_confirmation_and_notifies_old_address(self, notify_old, send_verify):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
        with self.captureOnCommitCallbacks(execute=True):
            changed = self.client.patch("/api/v1/accounts/me/settings/", {"full_name": "New Name", "phone": "0701234567", "preferred_language": "fa", "new_email": "new@example.com"}, format="json")
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.data["email"], "person@example.com")
        self.assertEqual(changed.data["pending_email"], "new@example.com")
        send_verify.assert_called_once_with(str(self.user.pk))
        self.user.refresh_from_db()
        token = make_email_change_token(self.user)
        with self.captureOnCommitCallbacks(execute=True):
            confirmed = self.client.post("/api/v1/accounts/email/confirm/", {"token": token}, format="json")
        self.assertEqual(confirmed.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "new@example.com")
        self.assertEqual(self.user.pending_email, "")
        notify_old.assert_called_once()
        self.assertIn("person@example.com", notify_old.call_args.args[3])

    def test_data_export_is_authenticated_and_contains_only_requester(self):
        other = User.objects.create_user(email="other@example.com", password="T9!Violet-Cedar-421", is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
        response = self.client.get("/api/v1/accounts/me/export/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("private, no-store", response["Cache-Control"])
        self.assertIn(self.user.email.encode(), response.content)
        self.assertNotIn(other.email.encode(), response.content)
