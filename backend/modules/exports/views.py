import base64
import hashlib
import json
from copy import deepcopy
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse
from rest_framework import generics, status
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from modules.billing.services import effective_entitlement
from modules.resumes.content import readiness
from modules.resumes.models import CVDocument
from .models import ExportJob
from .templates import TEMPLATE_CATALOG
from .serializers import CreateExportSerializer, ExportJobSerializer
from .tasks import render_export
from .quota import reserve_export, usage_for

class PreviewRenderThrottle(UserRateThrottle):
    scope = "preview"

class ExportRenderThrottle(UserRateThrottle):
    scope = "export"

class TemplateCatalogView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request):
        allowed = {"public-service-v1"}
        if request.user.is_authenticated:
            allowed = set(effective_entitlement(request.user)["plan"].allowed_templates)
        return Response([{"key": key, "version": value["version"], "name": value["name"],
            "description": value["description"], "access_level": value["access_level"],
            "supported_languages": value["supported_languages"], "layout_options": value["layout_options"],
            "theme_options": value["theme_options"], "font_options": value["font_options"],
            "is_available": key in allowed} for key, value in TEMPLATE_CATALOG.items()])

class ExportListCreateView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CreateExportSerializer
    def get_throttles(self):
        if self.request.method == "POST" and getattr(self.request, "data", {}).get("purpose") == ExportJob.PREVIEW:
            return [PreviewRenderThrottle()]
        return [ExportRenderThrottle()] if self.request.method == "POST" else []
    def get(self, request):
        jobs = ExportJob.objects.filter(owner=request.user).select_related("document")
        page = self.paginate_queryset(jobs)
        serializer = ExportJobSerializer(page if page is not None else jobs, many=True)
        return self.get_paginated_response(serializer.data) if page is not None else Response(serializer.data)
    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        document = generics.get_object_or_404(CVDocument.objects.select_for_update().filter(owner=request.user), pk=values["document_id"])
        if document.lifecycle_state == CVDocument.ARCHIVED:
            return Response({"detail": "Restore this CV before rendering.", "code": "archived", "fields": {}}, status=409)
        prior_key = ExportJob.objects.filter(owner=request.user, idempotency_key=values["idempotency_key"]).first()
        if prior_key:
            if prior_key.document_id != document.id or prior_key.purpose != values["purpose"] or prior_key.template_key != values["template_key"] or prior_key.format != values["format"] or prior_key.document_revision != document.revision:
                return Response({"detail": "This request key is already assigned to different render input.", "code": "idempotency_conflict", "fields": {}}, status=409)
            return Response(ExportJobSerializer(prior_key).data, status=202)
        resolved = effective_entitlement(request.user)
        plan = resolved["plan"]
        if values["template_key"] not in plan.allowed_templates or values["format"] not in plan.allowed_formats:
            return Response({"detail": "This template or format requires Premium access.", "code": "upgrade_required", "fields": {}}, status=403)
        if values["purpose"] == ExportJob.PREVIEW and values["format"] != ExportJob.PDF:
            return Response({"detail": "Previews are available as PDF.", "code": "preview_format_unsupported", "fields": {}}, status=400)
        readiness_result = readiness(document)
        if values["purpose"] == ExportJob.EXPORT and not readiness_result["ready"]:
            return Response({"detail": "Complete the required CV fields before exporting.", "code": "cv_incomplete", "fields": readiness_result["missing_fields"]}, status=400)
        frozen = {"snapshot": deepcopy(document.snapshot), "selected_sections": deepcopy(document.selected_sections), "title": document.title,
            "cv_type": document.cv_type, "output_language": document.output_language, "schema_version": document.schema_version,
            "template_version": document.template_version, "template_key": values["template_key"], "design_options": deepcopy(document.design_options), "format": values["format"], "watermark": plan.watermark_exports}
        photo = getattr(document, "photo", None)
        if photo and photo.file and values["template_key"] != "ats-v1":
            with photo.file.open("rb") as image_file:
                photo_bytes = image_file.read(512 * 1024 + 1)
            if len(photo_bytes) > 512 * 1024:
                return Response({"detail": "The saved photo is too large to embed in an export.", "code": "photo_too_large", "fields": {}}, status=400)
            frozen["photo_data"] = base64.b64encode(photo_bytes).decode("ascii")
        encoded = json.dumps(frozen, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        if values["purpose"] == ExportJob.PREVIEW:
            cached = ExportJob.objects.filter(owner=request.user, document=document, document_revision=document.revision,
                content_hash=digest, template_key=values["template_key"], format=values["format"], purpose=ExportJob.PREVIEW, status=ExportJob.SUCCEEDED).first()
            if cached:
                return Response(ExportJobSerializer(cached).data, status=200)
        else:
            existing = ExportJob.objects.filter(owner=request.user, document=document, document_revision=document.revision,
                content_hash=digest, template_key=values["template_key"], format=values["format"], purpose=ExportJob.EXPORT,
                status__in=[ExportJob.PENDING, ExportJob.PROCESSING, ExportJob.SUCCEEDED]).exclude(artifact="").first()
            if existing:
                return Response(ExportJobSerializer(existing).data, status=200 if existing.status == ExportJob.SUCCEEDED else 202)
        job = ExportJob.objects.create(owner=request.user, document=document, document_revision=document.revision,
            content_hash=digest, idempotency_key=values["idempotency_key"], purpose=values["purpose"],
            render_input=frozen, template_key=values["template_key"], format=values["format"])
        if values["purpose"] == ExportJob.EXPORT:
            reservation = reserve_export(request.user, job, plan)
            if reservation is False:
                job.delete()
                usage = usage_for(request.user)
                return Response({"detail": "Your rolling export limit is reached.", "code": "quota_exhausted", "fields": {},
                    "limit": plan.export_limit, "used": usage["used"], "reserved": usage["reserved"],
                    "next_available_at": usage["next_available_at"]}, status=429)
        transaction.on_commit(lambda: render_export.delay(str(job.pk)))
        return Response(ExportJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)

class ExportUsageView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        usage = usage_for(request.user)
        plan = usage["plan"]
        sub = usage["subscription"]
        return Response({"plan": {"code": plan.code, "name": plan.name, "export_limit": plan.export_limit,
            "rolling_window_hours": plan.rolling_window_hours, "allowed_formats": plan.allowed_formats,
            "allowed_templates": plan.allowed_templates, "watermark_exports": plan.watermark_exports},
            "subscription_status": sub.status if sub else "free", "subscription_expires_at": sub.expires_at if sub else None,
            "used": usage["used"], "reserved": usage["reserved"], "available": usage["available"],
            "next_available_at": usage["next_available_at"]})

class ExportJobDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        job = generics.get_object_or_404(ExportJob.objects.filter(owner=request.user), pk=id)
        return Response(ExportJobSerializer(job).data)

class ExportDownloadView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        job = generics.get_object_or_404(ExportJob.objects.filter(owner=request.user, purpose=ExportJob.EXPORT), pk=id)
        if job.status != ExportJob.SUCCEEDED or not job.artifact:
            return Response({"detail": "This export is not ready to download.", "code": "export_not_ready", "fields": {}}, status=409)
        mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" if job.format == ExportJob.DOCX else "application/pdf"
        ext = "docx" if job.format == ExportJob.DOCX else "pdf"
        response = FileResponse(job.artifact.open("rb"), content_type=mime, as_attachment=True, filename=f"{job.document.title}.{ext}")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response

class ExportPreviewView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        job = generics.get_object_or_404(ExportJob.objects.filter(owner=request.user, purpose=ExportJob.PREVIEW), pk=id)
        if job.status != ExportJob.SUCCEEDED or not job.artifact:
            return Response({"detail": "This preview is not ready.", "code": "preview_not_ready", "fields": {}}, status=409)
        response = FileResponse(job.artifact.open("rb"), content_type="application/pdf", as_attachment=False, filename="cv-preview.pdf")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
