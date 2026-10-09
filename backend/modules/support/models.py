import uuid
from django.db import models


class PublicContent(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    key = models.SlugField(max_length=24)
    version = models.CharField(max_length=40)
    status = models.CharField(max_length=12, choices=[(DRAFT, "Draft"), (PUBLISHED, "Published")], default=DRAFT)
    title_by_language = models.JSONField(default=dict)
    body_by_language = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key", "-updated_at"]
        constraints = [models.UniqueConstraint(fields=["key", "version"], name="unique_public_content_version")]


class ContactSubmission(models.Model):
    QUEUED = "queued"
    SENT = "sent"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender_email = models.EmailField()
    category = models.CharField(max_length=24)
    subject = models.CharField(max_length=160)
    message = models.TextField(max_length=5000)
    delivery_status = models.CharField(max_length=16, choices=[(QUEUED, "Queued"), (SENT, "Sent"), (UNAVAILABLE, "Unavailable"), (FAILED, "Failed")], default=QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
