from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()

class RegistrationTests(APITestCase):
    @patch("modules.accounts.views.send_activation_email.delay")
    def test_registration_creates_inactive_user_without_password(self, send_email):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post("/api/v1/accounts/register/", {
            "full_name": "Nasrat Nasrati", "email": " NASRAT@example.com ", "phone": "0701234567"
            }, format="json")
        self.assertEqual(response.status_code, 202)
        user = User.objects.get(email="nasrat@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.phone, "+93701234567")
        send_email.assert_called_once_with(str(user.pk))

    @patch("modules.accounts.views.send_activation_email.delay")
    def test_duplicate_email_has_generic_response_and_does_not_create_user(self, send_email):
        User.objects.create_user(email="nasrat@example.com", password="irrelevant", is_active=True)
        response = self.client.post("/api/v1/accounts/register/", {
            "full_name": "Another Name", "email": "NASRAT@example.com", "phone": "+93701234567"
        }, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(User.objects.filter(email="nasrat@example.com").count(), 1)
        self.assertIn("If this address can be registered", response.data["detail"])
        send_email.assert_not_called()

    def test_invalid_email_or_phone_is_rejected(self):
        response = self.client.post("/api/v1/accounts/register/", {
            "full_name": "A User", "email": "bad-email", "phone": "123"
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("fields", response.data)
        self.assertIn("phone", response.data["fields"])
