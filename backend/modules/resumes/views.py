import hashlib
import json
from copy import deepcopy
from django.db import transaction
from django.http import FileResponse
from rest_framework import filters, generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .content import BASE_SECTIONS, OPTIONAL_SECTIONS, readiness, validate_step
from .models import CVDocument, CVPhoto
from .photos import SafePhotoSerializer
from .serializers import (CreateBlankResumeSerializer, CreateResumeFromProfileSerializer,
    MetadataSerializer, ResumeDocumentSerializer, RevisionSerializer, WizardStepSerializer)
from .services import create_profile_snapshot
from .tasks import cleanup_private_file


def owned_document(request, id, lock=False):
    query = CVDocument.objects.filter(owner=request.user)
    if lock:
        query = query.select_for_update()
    return generics.get_object_or_404(query, pk=id)


def check_revision(document, data):
    request_id = data.get("request_id")
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    if request_id and document.last_write_id == request_id:
        if document.last_write_hash == digest:
            return Response(ResumeDocumentSerializer(document).data)
        return Response({"detail": "This request ID was already used for different changes.", "code": "request_conflict", "fields": {}}, status=409)
    if data["expected_revision"] != document.revision:
        return Response({"detail": "This CV changed in another session. Review the newer version before saving.", "code": "revision_conflict", "current_revision": document.revision, "fields": {}}, status=409)
    return None


def save_revision(document, data):
    document.revision += 1
    document.last_write_id = data.get("request_id")
    document.last_write_hash = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    document.save()


class ResumeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title"]
    ordering_fields = ["title", "created_at", "updated_at"]
    ordering = ["-updated_at"]
    def get_serializer_class(self):
        return CreateBlankResumeSerializer if self.request.method == "POST" else ResumeDocumentSerializer
    def get_queryset(self):
        queryset = CVDocument.objects.filter(owner=self.request.user).select_related("photo")
        state = self.request.query_params.get("state")
        return queryset.filter(lifecycle_state=state) if state in dict(CVDocument.LIFECYCLE_STATES) else queryset
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = CVDocument.objects.create(owner=request.user, snapshot={}, selected_sections=list(BASE_SECTIONS), **serializer.validated_data)
        return Response(ResumeDocumentSerializer(document).data, status=201)


class ResumeFromProfileView(generics.GenericAPIView):
    serializer_class = CreateResumeFromProfileSerializer
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = create_profile_snapshot(user=request.user, **serializer.validated_data)
        return Response(ResumeDocumentSerializer(document).data, status=201)


class ResumeDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MetadataSerializer
    def get(self, request, id):
        return Response(ResumeDocumentSerializer(owned_document(request, id)).data)
    @transaction.atomic
    def patch(self, request, id):
        document = owned_document(request, id, lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conflict = check_revision(document, serializer.validated_data)
        if conflict is not None:
            return conflict
        new_template = serializer.validated_data.get("template_key", document.template_key)
        next_design = serializer.validated_data.get("design_options", document.design_options)
        from modules.exports.templates import DEFAULT_DESIGN, DESIGN_OPTIONS, validate_design_options
        if "template_key" in serializer.validated_data and "design_options" not in serializer.validated_data:
            configured = DESIGN_OPTIONS[new_template]
            if next_design.get("theme") not in configured["themes"] or next_design.get("font") not in configured["fonts"] or next_design.get("layout") not in configured["layouts"]:
                next_design = dict(DEFAULT_DESIGN)
                if "single-column" in configured["layouts"]:
                    next_design["layout"] = "single-column"
        document.design_options = validate_design_options(new_template, next_design)
        for key in ("title", "cv_type", "output_language", "builder_step", "template_key"):
            if key in serializer.validated_data:
                setattr(document, key, serializer.validated_data[key])
        save_revision(document, serializer.validated_data)
        return Response(ResumeDocumentSerializer(document).data)
    @transaction.atomic
    def delete(self, request, id):
        document = owned_document(request, id, lock=True)
        serializer = RevisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conflict = check_revision(document, serializer.validated_data)
        if conflict is not None:
            return conflict
        document.delete()
        return Response(status=204)


class ResumeWizardStepView(generics.GenericAPIView):
    serializer_class = WizardStepSerializer
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def patch(self, request, id, step):
        document = owned_document(request, id, lock=True)
        if step not in range(1, 5):
            return Response({"detail": "Choose a step from 1 to 4.", "code": "invalid_step", "fields": {}}, status=400)
        if document.lifecycle_state == CVDocument.ARCHIVED:
            return Response({"detail": "Restore this CV before editing it.", "code": "archived", "fields": {}}, status=409)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        conflict = check_revision(document, data)
        if conflict is not None:
            return conflict
        values = validate_step(step, data["data"], complete=data["complete"])
        if step == 4:
            enabled_sections = values.get("enabled_sections", [section for section in OPTIONAL_SECTIONS if section in document.selected_sections])
            disabled_payload = set(values).intersection(OPTIONAL_SECTIONS) - set(enabled_sections)
            if disabled_payload:
                return Response({"detail": "Enable optional sections before saving their content.", "code": "section_not_selected", "fields": {key: ["Select this section first."] for key in disabled_payload}}, status=400)
        snapshot = deepcopy(document.snapshot)
        if step == 1:
            snapshot["personal"] = {**snapshot.get("personal", {}), **values}
        else:
            enabled = values.pop("enabled_sections", None)
            snapshot.update(values)
            if enabled is not None:
                document.selected_sections = list(BASE_SECTIONS) + enabled
        document.snapshot = snapshot
        document.builder_step = min(step + 1, 4) if data["complete"] else step
        if data["complete"]:
            document.last_completed_step = max(document.last_completed_step, step)
        save_revision(document, data)
        return Response(ResumeDocumentSerializer(document).data)


class ResumeReadinessView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, id):
        return Response(readiness(owned_document(request, id)))


class ResumeLifecycleViewSet(viewsets.GenericViewSet):
    serializer_class = RevisionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return CVDocument.objects.filter(owner=self.request.user)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def duplicate(self, request, pk=None):
        source = owned_document(request, pk, lock=True)
        clone = CVDocument.objects.create(owner=request.user, title=f"{source.title[:153]} (Copy)", cv_type=source.cv_type,
            output_language=source.output_language, schema_version=source.schema_version, template_version=source.template_version, template_key=source.template_key,
            selected_sections=deepcopy(source.selected_sections), snapshot=deepcopy(source.snapshot), design_options=deepcopy(source.design_options), builder_step=source.builder_step,
            last_completed_step=source.last_completed_step)
        return Response(ResumeDocumentSerializer(clone).data, status=201)
    def _state_change(self, request, pk, archive):
        document = owned_document(request, pk, lock=True)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conflict = check_revision(document, serializer.validated_data)
        if conflict is not None:
            return conflict
        if archive and document.lifecycle_state != CVDocument.ARCHIVED:
            document.state_before_archive = document.lifecycle_state
            document.lifecycle_state = CVDocument.ARCHIVED
        elif not archive and document.lifecycle_state == CVDocument.ARCHIVED:
            document.lifecycle_state = document.state_before_archive or CVDocument.DRAFT
            document.state_before_archive = ""
        save_revision(document, serializer.validated_data)
        return Response(ResumeDocumentSerializer(document).data)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def archive(self, request, pk=None):
        return self._state_change(request, pk, True)
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def restore(self, request, pk=None):
        return self._state_change(request, pk, False)


class ResumePhotoView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = SafePhotoSerializer
    def get(self, request, id):
        photo = generics.get_object_or_404(CVPhoto.objects.filter(document__owner=request.user), document_id=id)
        response = FileResponse(photo.file.open("rb"), content_type="image/jpeg")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
    @transaction.atomic
    def post(self, request, id):
        document = owned_document(request, id, lock=True)
        revision = RevisionSerializer(data=request.data)
        revision.is_valid(raise_exception=True)
        conflict = check_revision(document, revision.validated_data)
        if conflict is not None:
            return conflict
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo, _ = CVPhoto.objects.get_or_create(document=document)
        previous_name = photo.file.name
        photo.file = serializer.validated_data["photo"]
        photo.save(update_fields=["file"])
        if previous_name and previous_name != photo.file.name:
            transaction.on_commit(lambda: cleanup_private_file.delay(previous_name))
        save_revision(document, revision.validated_data)
        return Response(ResumeDocumentSerializer(document).data, status=201)
    @transaction.atomic
    def delete(self, request, id):
        document = owned_document(request, id, lock=True)
        revision = RevisionSerializer(data=request.query_params)
        revision.is_valid(raise_exception=True)
        conflict = check_revision(document, revision.validated_data)
        if conflict is not None:
            return conflict
        CVPhoto.objects.filter(document=document).delete()
        save_revision(document, revision.validated_data)
        return Response(ResumeDocumentSerializer(document).data)
