from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CareerProfile

User = get_user_model()

class CareerProfileTests(APITestCase):
    def test_profile_is_created_for_requester_and_afghan_fields_are_optional_private_by_default(self):
        user = User.objects.create_user(email="person@example.com", password="T9!Violet-Cedar-421", is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
        response = self.client.get("/api/v1/profiles/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["father_name"], "")
        self.assertEqual(response.data["tazkira_number"], "")
        self.assertFalse(response.data["show_father_name"])
        self.assertFalse(response.data["show_tazkira_number"])
        saved = self.client.patch("/api/v1/profiles/me/", {"professional_title": "Developer", "tazkira_number": "optional-id", "show_tazkira_number": False}, format="json")
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(CareerProfile.objects.get(user=user).tazkira_number, "optional-id")

    def test_each_requester_receives_only_their_profile(self):
        first = User.objects.create_user(email="first@example.com", password="T9!Violet-Cedar-421", is_active=True)
        second = User.objects.create_user(email="second@example.com", password="T9!Violet-Cedar-421", is_active=True)
        CareerProfile.objects.create(user=first, professional_title="Private title")
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(second).access_token}")
        response = self.client.get("/api/v1/profiles/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["professional_title"], "")
        self.assertNotEqual(response.data["id"], str(CareerProfile.objects.get(user=first).pk))

from rest_framework.test import APITestCase
from django.urls import reverse
from modules.accounts.models import User
from .models import CareerProfile, OptionalProfileEntry

class OptionalProfileEntryTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="profile-a@example.com", password="StrongPass123!", is_active=True)
        self.other = User.objects.create_user(email="profile-b@example.com", password="StrongPass123!", is_active=True)
        self.client.force_authenticate(self.user)
    def test_reference_contacts_require_explicit_consent(self):
        response = self.client.post("/api/v1/profiles/optional-entries/", {"entry_type":"reference", "title":"Referee", "referee_name":"Dr. Example", "referee_email":"ref@example.com"}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/v1/profiles/optional-entries/", {"entry_type":"reference", "title":"Referee", "referee_name":"Dr. Example", "referee_email":"ref@example.com", "consent_to_publish":True}, format="json")
        self.assertEqual(response.status_code, 201)
    def test_entries_are_owner_scoped_and_special_characters_are_safe(self):
        profile = CareerProfile.objects.create(user=self.other)
        entry = OptionalProfileEntry.objects.create(profile=profile, entry_type="project", title="Scholarship — O'Brien", description="研究 & <analysis>")
        response = self.client.get("/api/v1/profiles/optional-entries/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(str(entry.id), str(response.data))
        response = self.client.post("/api/v1/profiles/optional-entries/", {"entry_type":"project", "title":"Scholarship — O'Brien", "description":"研究 & <analysis>"}, format="json")
        self.assertEqual(response.status_code, 201)
