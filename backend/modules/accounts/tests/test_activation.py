from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from modules.accounts.tokens import make_activation_token

User = get_user_model()

class ActivationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password=None, is_active=False)
        self.token = make_activation_token(self.user)

    def test_valid_activation_sets_password_and_can_only_be_used_once(self):
        response = self.client.post("/api/v1/accounts/activate/", {"token": self.token, "password": "T9!Violet-Cedar-421"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.check_password("T9!Violet-Cedar-421"))
        repeated = self.client.post("/api/v1/accounts/activate/", {"token": self.token, "password": "T9!Violet-Cedar-421"}, format="json")
        self.assertEqual(repeated.status_code, 400)

    def test_altered_token_is_rejected(self):
        response = self.client.post("/api/v1/accounts/activate/", {"token": self.token + "x", "password": "T9!Violet-Cedar-421"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "invalid_activation")
