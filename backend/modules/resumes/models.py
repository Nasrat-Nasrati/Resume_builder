import uuid
from django.conf import settings
from django.db import models

def default_design_options():
    return {"theme": "blue-teal", "font": "sans", "layout": "classic"}

class CVDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_documents")
    title = models.CharField(max_length=160, default="Untitled CV")
    output_language = models.CharField(max_length=2, choices=[("en", "English"), ("fa", "Dari"), ("ps", "Pashto")], default="en")
    CV_TYPES = [("general", "General"), ("public_service", "Public service"), ("academic", "Academic"), ("scholarship", "Scholarship"), ("private_sector", "Private sector")]
    DRAFT = "draft"
    EXPORTED = "exported"
    ARCHIVED = "archived"
    LIFECYCLE_STATES = [(DRAFT, "Draft"), (EXPORTED, "Exported"), (ARCHIVED, "Archived")]
    cv_type = models.CharField(max_length=24, choices=CV_TYPES, default="general")
    lifecycle_state = models.CharField(max_length=16, choices=LIFECYCLE_STATES, default=DRAFT)
    state_before_archive = models.CharField(max_length=16, choices=LIFECYCLE_STATES, blank=True)
    schema_version = models.PositiveSmallIntegerField(default=1)
    template_version = models.PositiveSmallIntegerField(default=1)
    template_key = models.CharField(max_length=64, default="public-service-v1")
    design_options = models.JSONField(default=default_design_options)
    revision = models.PositiveIntegerField(default=1)
    last_write_id = models.UUIDField(null=True, blank=True)
    last_write_hash = models.CharField(max_length=64, blank=True)
    builder_step = models.PositiveSmallIntegerField(default=1)
    last_completed_step = models.PositiveSmallIntegerField(default=0)
    selected_sections = models.JSONField(default=list)
    snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["-updated_at"]


# Compatibility while the profile snapshot API transitions to the named document model.
ResumeDocument = CVDocument

class CVArtifact(models.Model):
    """Private generated file associated with a document; never expose storage names in API serializers."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name="artifacts")
    file = models.FileField(upload_to="resumes/private/")
    created_at = models.DateTimeField(auto_now_add=True)

class ExportCharge(models.Model):
    """Minimal quota history retained when a CV is deleted; deliberately has no CV foreign key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="export_charges")
    document_identity = models.UUIDField()
    charged_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "document_identity"], name="unique_export_charge_per_document")]
        indexes = [models.Index(fields=["owner", "expires_at"], name="export_charge_owner_expiry_idx")]

class CVPhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.OneToOneField(CVDocument, on_delete=models.CASCADE, related_name="photo")
    file = models.FileField(upload_to="resumes/private/photos/")
    created_at = models.DateTimeField(auto_now_add=True)
