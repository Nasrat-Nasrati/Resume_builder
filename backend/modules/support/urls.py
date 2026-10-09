from django.urls import path
from .views import ContactSubmissionView, PublicContentView, SupportDetailsView

urlpatterns = [
    path("contact/", ContactSubmissionView.as_view(), name="contact-submit"),
    path("details/", SupportDetailsView.as_view(), name="support-details"),
    path("content/<slug:key>/", PublicContentView.as_view(), name="public-content"),
]
