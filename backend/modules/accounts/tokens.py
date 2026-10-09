from django.core import signing

ACTIVATION_SALT = "kabulcv.accounts.activation.v1"
ACTIVATION_MAX_AGE = 60 * 60 * 24

def make_activation_token(user):
    return signing.dumps({"user_id": str(user.pk)}, salt=ACTIVATION_SALT, compress=True)

def read_activation_user(token):
    payload = signing.loads(token, salt=ACTIVATION_SALT, max_age=ACTIVATION_MAX_AGE)
    return payload["user_id"]

import hashlib
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

def make_password_reset_token(user):
    return urlsafe_base64_encode(force_bytes(user.pk)), default_token_generator.make_token(user)

def reset_cooldown_key(purpose, email):
    return f"kabulcv:{purpose}:{hashlib.sha256(email.encode('utf-8')).hexdigest()}"

EMAIL_CHANGE_SALT = "kabulcv.accounts.email-change.v1"

def make_email_change_token(user):
    return signing.dumps({"user_id": str(user.pk), "email": user.pending_email}, salt=EMAIL_CHANGE_SALT, compress=True)

def read_email_change_token(token):
    return signing.loads(token, salt=EMAIL_CHANGE_SALT, max_age=60 * 60 * 24)
