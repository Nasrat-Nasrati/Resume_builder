from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import exception_handler
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request):
    return Response({"status": "ok", "service": "kabulcv-api"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health, name="health"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/accounts/", include("modules.accounts.urls")),
    path("api/v1/profiles/", include("modules.profiles.urls")),
    path("api/v1/resumes/", include("modules.resumes.urls")),
    path("api/v1/exports/", include("modules.exports.urls")),
    path("api/v1/billing/", include("modules.billing.urls")),
    path("api/v1/analytics/", include("modules.analytics.urls")),
    path("api/v1/support/", include("modules.support.urls")),
]
