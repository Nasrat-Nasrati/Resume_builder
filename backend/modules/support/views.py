from django.conf import settings
from django.db import transaction
from django.http import Http404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import ContactSubmission, PublicContent
from .serializers import ContactSubmissionResultSerializer, ContactSubmissionSerializer
from .tasks import send_contact_notification


class ContactThrottle(AnonRateThrottle):
    scope = "contact"


class PublicContentView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request, key):
        content = PublicContent.objects.filter(key=key).order_by("-updated_at").first()
        if content is None:
            raise Http404
        language = request.query_params.get("lang", "en")
        if language not in {"en", "fa", "ps"}:
            language = "en"
        data = {"key": content.key, "version": content.version, "status": content.status, "language": language,
            "title": content.title_by_language.get(language) or content.title_by_language.get("en", ""),
            "body": content.body_by_language.get(language) or content.body_by_language.get("en", [])}
        response = Response(data)
        response["Cache-Control"] = "public, max-age=300"
        response["Vary"] = "Accept-Language"
        return response


class SupportDetailsView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    def get(self, request):
        data = {"email": settings.SUPPORT_EMAIL or None, "whatsapp_url": settings.SUPPORT_WHATSAPP_URL or None,
            "telegram_url": settings.SUPPORT_TELEGRAM_URL or None, "office_address": settings.SUPPORT_OFFICE_ADDRESS or None}
        response = Response(data)
        response["Cache-Control"] = "public, max-age=300"
        return response


class ContactSubmissionView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    throttle_classes = [ContactThrottle]
    serializer_class = ContactSubmissionSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        if values.pop("website", ""):
            return Response({"detail": "Your message has been received."}, status=status.HTTP_202_ACCEPTED)
        delivery = ContactSubmission.QUEUED if settings.SUPPORT_EMAIL else ContactSubmission.UNAVAILABLE
        submission = ContactSubmission.objects.create(**values, delivery_status=delivery)
        if settings.SUPPORT_EMAIL:
            def enqueue_delivery():
                try:
                    send_contact_notification.delay(str(submission.pk))
                except Exception:
                    ContactSubmission.objects.filter(pk=submission.pk, delivery_status=ContactSubmission.QUEUED).update(delivery_status=ContactSubmission.FAILED)
            transaction.on_commit(enqueue_delivery)
        response = Response(ContactSubmissionResultSerializer(submission).data, status=status.HTTP_202_ACCEPTED)
        response["Cache-Control"] = "private, no-store"
        return response
