from django.utils.cache import patch_vary_headers


PUBLIC_CACHE_PATHS = {
    "/api/v1/health/", "/api/v1/billing/plans/", "/api/v1/billing/readiness/",
    "/api/v1/analytics/stats/", "/api/v1/support/details/",
}


class PrivateApiNoStoreMiddleware:
    """Keep API responses private by default; only explicit safe GET endpoints may cache."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            if request.method == "GET" and (request.path in PUBLIC_CACHE_PATHS or request.path.startswith("/api/v1/support/content/")):
                response.setdefault("Cache-Control", "public, max-age=60")
            else:
                response["Cache-Control"] = "private, no-store"
            if request.path == "/api/v1/exports/templates/":
                patch_vary_headers(response, ["Authorization", "Cookie"])
        return response
