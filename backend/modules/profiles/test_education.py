from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CareerProfile, EducationRecord

User = get_user_model()

class EducationRecordTests(APITestCase):
    def setUp(self):
        self.user=User.objects.create_user(email="student@example.com",password="T9!Violet-Cedar-421",is_active=True)
        self.profile=CareerProfile.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(self.user).access_token}")
        self.url="/api/v1/profiles/education/"

    def payload(self,**updates):
        body={"record_type":"education","qualification":"Bachelor","field_of_study":"Computing","institution":"Unlisted Institute","location":"Kabul","start_date":"2020-01-01","end_date":"2024-01-01","is_current":False,"credential_reference":"","sort_order":0};body.update(updates);return body

    def test_manual_institution_saves_invalid_dates_fail_and_suggestions_are_owned(self):
        invalid=self.client.post(self.url,self.payload(end_date="2019-01-01"),format="json")
        self.assertEqual(invalid.status_code,400)
        saved=self.client.post(self.url,self.payload(),format="json")
        self.assertEqual(saved.status_code,201)
        self.assertEqual(saved.data["institution"],"Unlisted Institute")
        suggestions=self.client.get(self.url+"institutions/?q=Unlisted")
        self.assertEqual(suggestions.data,["Unlisted Institute"])

    def test_order_and_delete_are_persisted_and_other_users_are_scoped(self):
        one=EducationRecord.objects.create(profile=self.profile,qualification="One",institution="A")
        two=EducationRecord.objects.create(profile=self.profile,qualification="Two",institution="B")
        response=self.client.post(self.url+"reorder/",{"ids":[str(two.pk),str(one.pk)]},format="json")
        self.assertEqual(response.status_code,200)
        one.refresh_from_db();two.refresh_from_db()
        self.assertEqual([two.sort_order,one.sort_order],[0,1])
        other=User.objects.create_user(email="other@example.com",password="T9!Violet-Cedar-421",is_active=True)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(other).access_token}")
        self.assertEqual(self.client.get(self.url+f"{one.pk}/").status_code,404)
