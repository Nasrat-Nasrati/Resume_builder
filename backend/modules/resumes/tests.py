from rest_framework.test import APITestCase
from modules.accounts.models import User
from modules.profiles.models import CareerProfile, Experience
from .models import ResumeDocument

class ProfileSnapshotTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="snapshot@example.com", password="StrongPass123!", is_active=True)
        self.other = User.objects.create_user(email="other-snapshot@example.com", password="StrongPass123!", is_active=True)
        profile = CareerProfile.objects.create(user=self.user, professional_title="Engineer")
        self.experience = Experience.objects.create(profile=profile, position="Developer", employer="Example", start_date="2020-01-01", duties="Built apps")
    def test_selected_data_is_copied_and_immutable_from_profile_edits(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/resumes/from-profile/", {"title":"Scholarship CV", "output_language":"en", "selected_sections":["profile", "experience"]}, format="json")
        self.assertEqual(response.status_code, 201)
        resume_id = response.data["id"]
        self.experience.delete()
        self.assertEqual(ResumeDocument.objects.get(pk=resume_id).snapshot["experience"][0]["position"], "Developer")
    def test_user_cannot_read_another_users_resume(self):
        resume = ResumeDocument.objects.create(owner=self.other, snapshot={"profile":{"professional_title":"Private"}})
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"/api/v1/resumes/{resume.id}/").status_code, 404)
    def test_disabled_optional_section_cannot_be_selected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/resumes/from-profile/", {"selected_sections":["projects"]}, format="json")
        self.assertEqual(response.status_code, 400)
    def test_revision_starts_at_one_and_archive_restore_are_owner_scoped(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/resumes/from-profile/", {"selected_sections":["profile"]}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["revision"], 1)
        resume_id = response.data["id"]
        archived = self.client.post(f"/api/v1/resumes/lifecycle/{resume_id}/archive/", {"expected_revision": 1}, format="json")
        self.assertEqual(archived.data["lifecycle_state"], "archived")
        restored = self.client.post(f"/api/v1/resumes/lifecycle/{resume_id}/restore/", {"expected_revision": 2}, format="json")
        self.assertEqual(restored.data["lifecycle_state"], "draft")
        foreign = ResumeDocument.objects.create(owner=self.other)
        self.assertEqual(self.client.post(f"/api/v1/resumes/lifecycle/{foreign.id}/archive/", {"expected_revision": 1}, format="json").status_code, 404)

    def test_blank_resume_is_created_with_empty_content_schema(self):
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/resumes/", {"title":"Blank draft", "output_language":"fa", "cv_type":"scholarship"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["snapshot"], {})
        self.assertEqual(response.data["revision"], 1)
        self.assertEqual(response.data["cv_type"], "scholarship")

    def test_duplicate_gets_new_id_draft_and_rename_preserves_snapshot(self):
        original = ResumeDocument.objects.create(owner=self.user, title="Original", snapshot={"profile":{"professional_title":"Engineer"}}, selected_sections=["profile"], lifecycle_state="exported", revision=7)
        self.client.force_authenticate(self.user)
        response = self.client.post(f"/api/v1/resumes/lifecycle/{original.id}/duplicate/")
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data["id"], str(original.id))
        self.assertEqual(response.data["revision"], 1)
        self.assertEqual(response.data["lifecycle_state"], "draft")
        duplicate_id = response.data["id"]
        response = self.client.patch(f"/api/v1/resumes/{duplicate_id}/", {"title":"Scholarship CV", "expected_revision": 1}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["snapshot"], original.snapshot)
        self.assertEqual(response.data["title"], "Scholarship CV")

    def test_delete_removes_document_but_keeps_minimal_export_charge(self):
        from django.utils import timezone
        from datetime import timedelta
        from .models import ExportCharge
        document = ResumeDocument.objects.create(owner=self.user, snapshot={"profile":{"summary":"private"}})
        ExportCharge.objects.create(owner=self.user, document_identity=document.id, expires_at=timezone.now()+timedelta(hours=24))
        self.client.force_authenticate(self.user)
        response = self.client.delete(f"/api/v1/resumes/{document.id}/", {"expected_revision": document.revision}, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ResumeDocument.objects.filter(pk=document.id).exists())
        self.assertTrue(ExportCharge.objects.filter(owner=self.user, document_identity=document.id).exists())
    def test_builder_step_persists_and_foreign_resume_is_not_found(self):
        document = ResumeDocument.objects.create(owner=self.user)
        self.client.force_authenticate(self.user)
        response = self.client.patch(f"/api/v1/resumes/{document.id}/", {"builder_step":3, "expected_revision":1}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["builder_step"], 3)
        other_doc = ResumeDocument.objects.create(owner=self.other)
        self.assertEqual(self.client.get(f"/api/v1/resumes/{other_doc.id}/").status_code, 404)

    def test_incomplete_step_saves_and_completion_validates_required_fields(self):
        document = ResumeDocument.objects.create(owner=self.user)
        self.client.force_authenticate(self.user)
        path = f"/api/v1/resumes/{document.id}/steps/1/"
        response = self.client.patch(path, {"expected_revision":1, "data":{"professional_title":"Engineer"}, "complete":False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["builder_step"], 1)
        self.assertEqual(response.data["revision"], 2)
        response = self.client.patch(path, {"expected_revision":2, "data":{"professional_title":"Engineer"}, "complete":True}, format="json")
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(path, {"expected_revision":2, "data":{"full_name":"Nasrat"}, "complete":True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["last_completed_step"], 1)
        self.assertEqual(response.data["builder_step"], 2)

    def test_photo_requires_real_image_and_is_served_only_to_owner(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from .models import CVPhoto
        document = ResumeDocument.objects.create(owner=self.user)
        self.client.force_authenticate(self.user)
        disguised = SimpleUploadedFile("fake.png", b"<svg><script>alert(1)</script></svg>", content_type="image/png")
        response = self.client.post(f"/api/v1/resumes/{document.id}/photo/", {"photo":disguised}, format="multipart")
        self.assertEqual(response.status_code, 400)
        other_doc = ResumeDocument.objects.create(owner=self.other)
        self.assertEqual(self.client.get(f"/api/v1/resumes/{other_doc.id}/photo/").status_code, 404)
    def test_experience_step_saves_ordered_plain_text_and_validates_current_dates(self):
        document = ResumeDocument.objects.create(owner=self.user)
        self.client.force_authenticate(self.user)
        url = f"/api/v1/resumes/{document.id}/steps/2/"
        entries = [{"position":"Developer", "employer":"Example", "start_date":"2022-01-01", "end_date":None, "is_current":True, "duties":"Built <platform> & tools"}]
        response = self.client.patch(url, {"expected_revision":1, "data":{"experience":entries}, "complete":True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["snapshot"]["experience"][0]["duties"], "Built <platform> & tools")
        invalid = [{"position":"Developer", "employer":"Example", "start_date":"2024-01-01", "end_date":"2023-01-01", "is_current":False}]
        response = self.client.patch(url, {"expected_revision":2, "data":{"experience":invalid}, "complete":True}, format="json")
        self.assertEqual(response.status_code, 400)
    def test_education_language_and_optional_snapshot_fields_validate(self):
        document = ResumeDocument.objects.create(owner=self.user, selected_sections=["profile", "education", "languages", "skills", "publications"])
        self.client.force_authenticate(self.user)
        response = self.client.patch(f"/api/v1/resumes/{document.id}/steps/3/", {"expected_revision":1, "data":{"education":[{"record_type":"education", "qualification":"BSc", "institution":"Manual University", "start_date":"2018-01-01", "end_date":"2022-01-01"}]}, "complete":True}, format="json")
        self.assertEqual(response.status_code, 200)
        data = {"skills":[{"name":"Technical", "skills":["Python"]}], "languages":[{"language":"Dari", "is_mother_tongue":True, "proficiency":""}], "publications":[{"title":"Research work"}]}
        response = self.client.patch(f"/api/v1/resumes/{document.id}/steps/4/", {"expected_revision":2, "data":data, "complete":True}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("languages", response.data["snapshot"])
        self.assertIn("publications", response.data["snapshot"])
        response = self.client.patch(f"/api/v1/resumes/{document.id}/steps/4/", {"expected_revision":3, "data":{"projects":[]}, "complete":False}, format="json")
        self.assertEqual(response.status_code, 400)
