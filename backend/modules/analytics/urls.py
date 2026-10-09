from django.urls import path
from .views import PublicPageViewView, PublicStatsView

urlpatterns = [
    path("stats/", PublicStatsView.as_view(), name="public-stats"),
    path("page-views/", PublicPageViewView.as_view(), name="public-page-view"),
]
