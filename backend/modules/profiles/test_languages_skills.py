from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CareerProfile, LanguageEntry, SkillGroup

User=get_user_model()
class LanguageAndSkillTests(APITestCase):
    def setUp(self):
        self.user=User.objects.create_user(email="person@example.com",password="T9!Violet-Cedar-421",is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
    def test_mother_tongue_needs_no_level_and_cefr_is_validated(self):
        url="/api/v1/profiles/languages/"
        mother=self.client.post(url,{"language":"Dari","is_mother_tongue":True,"proficiency":"","cefr_level":"","sort_order":0},format="json")
        self.assertEqual(mother.status_code,201)
        invalid=self.client.post(url,{"language":"English","is_mother_tongue":False,"proficiency":"fluent","cefr_level":"C3","sort_order":1},format="json")
        self.assertEqual(invalid.status_code,400)
        duplicate=self.client.post(url,{"language":"dari","is_mother_tongue":True,"proficiency":"","cefr_level":"","sort_order":1},format="json")
        self.assertEqual(duplicate.status_code,400)
    def test_skill_group_and_skills_are_scoped_to_profile_owner(self):
        profile=CareerProfile.objects.create(user=self.user)
        group=SkillGroup.objects.create(profile=profile,name="Technical")
        denied=User.objects.create_user(email="other@example.com",password="T9!Violet-Cedar-421",is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(denied).access_token}")
        response=self.client.post("/api/v1/profiles/skills/",{"group":str(group.pk),"name":"Python","sort_order":0},format="json")
        self.assertEqual(response.status_code,400)
