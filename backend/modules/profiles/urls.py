from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import CareerProfileView, ExperienceViewSet, EducationRecordViewSet, LanguageEntryViewSet, SkillGroupViewSet, SkillViewSet, OptionalProfileEntryViewSet

router = DefaultRouter()
router.register("experience", ExperienceViewSet, basename="experience")
router.register("education", EducationRecordViewSet, basename="education-record")
router.register("languages", LanguageEntryViewSet, basename="language-entry")
router.register("skill-groups", SkillGroupViewSet, basename="skill-group")
router.register("skills", SkillViewSet, basename="skill")
router.register("optional-entries", OptionalProfileEntryViewSet, basename="optional-profile-entry")
urlpatterns = [path("me/", CareerProfileView.as_view(), name="career-profile"), path("", include(router.urls))]
