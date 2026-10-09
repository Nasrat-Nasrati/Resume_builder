from django.urls import path
from .views import ExportDownloadView, ExportJobDetailView, ExportListCreateView, ExportPreviewView, ExportUsageView, TemplateCatalogView

urlpatterns = [
    path("", ExportListCreateView.as_view(), name="export-list-create"),
    path("usage/", ExportUsageView.as_view(), name="export-usage"),
    path("templates/", TemplateCatalogView.as_view(), name="template-catalog"),
    path("<uuid:id>/download/", ExportDownloadView.as_view(), name="export-download"),
    path("<uuid:id>/preview/", ExportPreviewView.as_view(), name="export-preview"),
    path("<uuid:id>/", ExportJobDetailView.as_view(), name="export-detail"),
]
