import smtplib
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from .models import ContactSubmission


@shared_task(bind=True, autoretry_for=(OSError, smtplib.SMTPException), retry_backoff=True, retry_jitter=True, max_retries=5)
def send_contact_notification(self, submission_id):
    submission = ContactSubmission.objects.get(pk=submission_id)
    if not settings.SUPPORT_EMAIL:
        submission.delivery_status = ContactSubmission.UNAVAILABLE
        submission.save(update_fields=["delivery_status"])
        return submission.id
    try:
        sent = send_mail(
            subject=f"KabulCV support: {submission.category} — {submission.subject}",
            message=f"Reply to: {submission.sender_email}\nCategory: {submission.category}\n\n{submission.message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.SUPPORT_EMAIL],
            fail_silently=False,
        )
        submission.delivery_status = ContactSubmission.SENT if sent else ContactSubmission.FAILED
        submission.save(update_fields=["delivery_status"])
    except (OSError, smtplib.SMTPException):
        if self.request.retries >= self.max_retries:
            submission.delivery_status = ContactSubmission.FAILED
            submission.save(update_fields=["delivery_status"])
        raise
    return submission.id
