from django.urls import path
from .views import ResumeListCreateView, ResumeFromProfileView, ResumeDetailView, ResumeLifecycleViewSet, ResumeWizardStepView, ResumePhotoView, ResumeReadinessView
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register("lifecycle", ResumeLifecycleViewSet, basename="resume-lifecycle")
urlpatterns = [
    path("", ResumeListCreateView.as_view(), name="resume-list"),
    path("from-profile/", ResumeFromProfileView.as_view(), name="resume-from-profile"),
    path("<uuid:id>/readiness/", ResumeReadinessView.as_view(), name="resume-readiness"),
    path("<uuid:id>/photo/", ResumePhotoView.as_view(), name="resume-photo"),
    path("<uuid:id>/steps/<int:step>/", ResumeWizardStepView.as_view(), name="resume-wizard-step"),
    path("<uuid:id>/", ResumeDetailView.as_view(), name="resume-detail"),
] + router.urls
