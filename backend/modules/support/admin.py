from django.contrib import admin
from .models import ContactSubmission, PublicContent


@admin.register(PublicContent)
class PublicContentAdmin(admin.ModelAdmin):
    list_display = ("key", "version", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("key", "version")


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "sender_email", "category", "delivery_status")
    list_filter = ("category", "delivery_status", "created_at")
    search_fields = ("sender_email", "subject")
    readonly_fields = ("id", "sender_email", "category", "subject", "message", "created_at")
