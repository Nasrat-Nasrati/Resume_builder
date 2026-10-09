from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CareerProfile, Experience

User = get_user_model()

class ExperienceTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="person@example.com", password="T9!Violet-Cedar-421", is_active=True)
        self.profile = CareerProfile.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
        self.url = "/api/v1/profiles/experience/"

    def payload(self, **changes):
        data = {"position": "Developer", "employer": "Example Org", "location": "Kabul", "start_date": "2023-01-01", "end_date": "2024-01-01", "is_current": False, "duties": "Built tools", "sort_order": 0}
        data.update(changes)
        return data

    def test_end_before_start_is_rejected_and_current_job_omits_end(self):
        invalid = self.client.post(self.url, self.payload(end_date="2022-01-01"), format="json")
        self.assertEqual(invalid.status_code, 400)
        current = self.client.post(self.url, self.payload(end_date=None, is_current=True), format="json")
        self.assertEqual(current.status_code, 201)
        self.assertIsNone(current.data["end_date"])

    def test_ordering_persists_and_other_users_cannot_read_entry(self):
        first = Experience.objects.create(profile=self.profile, position="First", employer="Org", start_date=date(2020, 1, 1), sort_order=0)
        second = Experience.objects.create(profile=self.profile, position="Second", employer="Org", start_date=date(2021, 1, 1), sort_order=1)
        response = self.client.post(self.url + "reorder/", {"ids": [str(second.pk), str(first.pk)]}, format="json")
        self.assertEqual(response.status_code, 200)
        first.refresh_from_db(); second.refresh_from_db()
        self.assertEqual([second.sort_order, first.sort_order], [0, 1])
        other = User.objects.create_user(email="other@example.com", password="T9!Violet-Cedar-421", is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
        denied = self.client.get(self.url + f"{first.pk}/")
        self.assertEqual(denied.status_code, 404)
