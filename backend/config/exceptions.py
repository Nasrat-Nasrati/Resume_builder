from rest_framework.views import exception_handler as drf_exception_handler


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if isinstance(data, dict) and "detail" in data:
        detail = str(data["detail"])
        code = getattr(data["detail"], "code", "request_error")
        fields = {}
    elif isinstance(data, dict):
        detail, code, fields = "Validation failed.", "validation_error", data
    else:
        detail, code, fields = str(data), "request_error", {}
    response.data = {"detail": detail, "code": str(code), "fields": fields}
    return response
