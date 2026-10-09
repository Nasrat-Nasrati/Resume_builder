from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

User = get_user_model()

class SessionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="T9!Violet-Cedar-421", is_active=True)
        self.client = APIClient(enforce_csrf_checks=True)

    def test_inactive_account_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post("/api/v1/accounts/auth/login/", {"email": self.user.email, "password": "T9!Violet-Cedar-421"}, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "invalid_credentials")

    def test_login_refresh_rotation_and_logout_revoke_refresh(self):
        login = self.client.post("/api/v1/accounts/auth/login/", {"email": self.user.email, "password": "T9!Violet-Cedar-421"}, format="json")
        self.assertEqual(login.status_code, 200)
        self.assertIn("access", login.data)
        self.assertTrue(login.cookies["kabulcv_refresh"]["httponly"])
        self.assertIn("csrftoken", self.client.cookies)
        old_refresh = login.cookies["kabulcv_refresh"].value
        csrf = self.client.cookies["csrftoken"].value
        denied = self.client.post("/api/v1/accounts/auth/refresh/", {}, format="json")
        self.assertEqual(denied.status_code, 403)
        refreshed = self.client.post("/api/v1/accounts/auth/refresh/", {}, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("access", refreshed.data)
        new_refresh = refreshed.cookies["kabulcv_refresh"].value
        self.assertNotEqual(old_refresh, new_refresh)
        self.client.cookies["kabulcv_refresh"] = new_refresh
        logout = self.client.post("/api/v1/accounts/auth/logout/", {}, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(logout.status_code, 204)
        self.client.cookies["kabulcv_refresh"] = new_refresh
        after_logout = self.client.post("/api/v1/accounts/auth/refresh/", {}, format="json", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(after_logout.status_code, 401)
