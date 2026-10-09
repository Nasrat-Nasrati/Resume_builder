from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from .models import User
from .tokens import make_activation_token

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_activation_email(self, user_id):
    user = User.objects.get(pk=user_id, is_active=False)
    token = make_activation_token(user)
    activation_url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/activate?token={token}"
    message = render_to_string("accounts/activation_email.txt", {"first_name": user.first_name, "activation_url": activation_url})
    send_mail(
        subject="Activate your KabulCV account",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email], fail_silently=False,
    )

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_password_reset_email(self, user_id):
    user = User.objects.get(pk=user_id, is_active=True)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/reset-password?uid={uid}&token={token}"
    send_mail("Reset your KabulCV password", f"Hello {user.first_name},\n\nUse this link to choose a new password (valid for one hour):\n{reset_url}\n\nIf you did not request this, ignore this email.", settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

from .tokens import make_email_change_token

@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def send_email_change_verification(self, user_id):
    user = User.objects.get(pk=user_id)
    if not user.pending_email:
        return
    token = make_email_change_token(user)
    url = f"{settings.PUBLIC_APP_URL.rstrip('/')}/settings?email_token={token}"
    send_mail("Confirm your new KabulCV email", f"Confirm this email change within 24 hours: {url}", settings.DEFAULT_FROM_EMAIL, [user.pending_email], fail_silently=False)
