import uuid
from django.conf import settings
from django.db import models

def private_artifact_path(instance, filename):
    folder = "previews" if instance.purpose == ExportJob.PREVIEW else "exports"
    extension = "docx" if instance.format == ExportJob.DOCX else "pdf"
    return f"resumes/private/{folder}/{instance.pk}.{extension}"

class ExportJob(models.Model):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    STATUSES = [(value, value.title()) for value in (PENDING, PROCESSING, SUCCEEDED, FAILED)]
    PDF = "pdf"
    DOCX = "docx"
    PREVIEW = "preview"
    EXPORT = "export"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="export_jobs")
    document = models.ForeignKey("resumes.CVDocument", on_delete=models.CASCADE, related_name="export_jobs")
    format = models.CharField(max_length=8, default=PDF, choices=[(PDF, "PDF"), (DOCX, "Word document")])
    purpose = models.CharField(max_length=12, choices=[(PREVIEW, "Preview"), (EXPORT, "Export")], default=EXPORT)
    status = models.CharField(max_length=16, choices=STATUSES, default=PENDING)
    document_revision = models.PositiveIntegerField(default=1)
    content_hash = models.CharField(max_length=64, default="")
    idempotency_key = models.UUIDField(null=True, blank=True)
    # Frozen at request time; retries never render newer CV data.
    render_input = models.JSONField()
    template_key = models.CharField(max_length=64, default="public-service-v1")
    artifact = models.FileField(upload_to=private_artifact_path, blank=True)
    failure_code = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["owner", "idempotency_key"], condition=models.Q(idempotency_key__isnull=False), name="export_owner_idempotency_key_unique")]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            previous = type(self).objects.only("purpose", "format", "document_revision", "content_hash", "template_key", "render_input").get(pk=self.pk)
            immutable = ("purpose", "format", "document_revision", "content_hash", "template_key", "render_input")
            if any(getattr(previous, key) != getattr(self, key) for key in immutable):
                raise ValueError("Export render input is immutable.")
        return super().save(*args, **kwargs)


class ExportReservation(models.Model):
    RESERVED = "reserved"
    SETTLED = "settled"
    RELEASED = "released"
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="export_reservations")
    document_identity = models.UUIDField()
    job = models.ForeignKey(ExportJob, on_delete=models.CASCADE, related_name="reservations")
    status = models.CharField(max_length=12, choices=[(RESERVED, "Reserved"), (SETTLED, "Settled"), (RELEASED, "Released")], default=RESERVED)
    reserved_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["owner", "document_identity"], condition=models.Q(status="reserved"), name="one_active_export_reservation_per_cv")]
        indexes = [models.Index(fields=["owner", "status", "expires_at"], name="export_reservation_owner_idx")]
