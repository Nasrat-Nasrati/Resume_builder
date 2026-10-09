from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core import signing
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import RegistrationSerializer, ActivateAccountSerializer
from .tasks import send_activation_email
from .tokens import read_activation_user

class RegistrationThrottle(AnonRateThrottle):
    scope = "registration"

class ActivationThrottle(AnonRateThrottle):
    scope = "activation"

class LoginThrottle(AnonRateThrottle):
    scope = "login"

class RefreshThrottle(AnonRateThrottle):
    scope = "refresh"

@extend_schema(request=RegistrationSerializer, responses={202: None})
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RegistrationThrottle])
def register(request):
    serializer = RegistrationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = None
    try:
        with transaction.atomic():
            email = serializer.validated_data["email"]
            existing = User.objects.filter(email=email).first()
            if existing is None:
                user = serializer.save()
                transaction.on_commit(lambda: send_activation_email.delay(str(user.pk)))
    except IntegrityError:
        # A concurrent request may have claimed the normalized email.
        pass
    return Response({"detail": _("If this address can be registered, an activation email will be sent.")}, status=status.HTTP_202_ACCEPTED)

@extend_schema(request=ActivateAccountSerializer, responses={200: None})
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([ActivationThrottle])
def activate(request):
    serializer = ActivateAccountSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user_id = read_activation_user(serializer.validated_data["token"])
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_id, is_active=False)
            password_validation.validate_password(serializer.validated_data["password"], user=user)
            user.set_password(serializer.validated_data["password"])
            user.is_active = True
            user.activated_at = timezone.now()
            user.save(update_fields=["password", "is_active", "activated_at", "updated_at"])
    except DjangoValidationError as exc:
        return Response({"detail": _("The password does not meet the requirements."), "code": "invalid_password", "fields": {"password": exc.messages}}, status=status.HTTP_400_BAD_REQUEST)
    except (signing.BadSignature, signing.SignatureExpired, KeyError, User.DoesNotExist):
        return Response({"detail": _("This activation link is invalid, expired, or already used."), "code": "invalid_activation", "fields": {}}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": _("Your account is active. You can now sign in.")})


def _set_refresh_cookie(response, token):
        response.set_cookie(settings.JWT_REFRESH_COOKIE, token, max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
                        httponly=True, secure=settings.JWT_COOKIE_SECURE, samesite=settings.JWT_COOKIE_SAMESITE, path=settings.JWT_REFRESH_COOKIE_PATH)

def _csrf_failure(request):
    middleware = CsrfViewMiddleware(lambda req: Response(status=204))
    return middleware.process_view(request._request, lambda req: Response(status=204), (), {})

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    email = str(request.data.get("email", "")).strip().lower()
    password = request.data.get("password", "")
    user = authenticate(request._request, email=email, password=password)
    if user is None or not user.is_active:
        return Response({"detail": _("Email or password is incorrect."), "code": "invalid_credentials", "fields": {}}, status=status.HTTP_401_UNAUTHORIZED)
    refresh = RefreshToken.for_user(user)
    response = Response({"access": str(refresh.access_token), "user": {"id": str(user.pk), "email": user.email, "first_name": user.first_name, "last_name": user.last_name, "preferred_language": user.preferred_language}})
    get_token(request._request)
    _set_refresh_cookie(response, str(refresh))
    return response

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RefreshThrottle])
def refresh_session(request):
    csrf_response = _csrf_failure(request)
    if csrf_response is not None:
        return Response({"detail": _("CSRF verification failed."), "code": "csrf_failed", "fields": {}}, status=status.HTTP_403_FORBIDDEN)
    from django.conf import settings
    raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
    if not raw_refresh:
        return Response({"detail": _("Your session has expired."), "code": "session_expired", "fields": {}}, status=status.HTTP_401_UNAUTHORIZED)
    serializer = TokenRefreshSerializer(data={"refresh": raw_refresh})
    try:
        serializer.is_valid(raise_exception=True)
    except Exception:
        response = Response({"detail": _("Your session has expired."), "code": "session_expired", "fields": {}}, status=status.HTTP_401_UNAUTHORIZED)
        response.delete_cookie(settings.JWT_REFRESH_COOKIE, path=settings.JWT_REFRESH_COOKIE_PATH, samesite=settings.JWT_COOKIE_SAMESITE)
        return response
    data = {"access": serializer.validated_data["access"]}
    response = Response(data)
    rotated = serializer.validated_data.get("refresh")
    if rotated:
        _set_refresh_cookie(response, rotated)
    return response

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RefreshThrottle])
def logout(request):
    csrf_response = _csrf_failure(request)
    if csrf_response is not None:
        return Response({"detail": _("CSRF verification failed."), "code": "csrf_failed", "fields": {}}, status=status.HTTP_403_FORBIDDEN)
    from django.conf import settings
    raw_refresh = request.COOKIES.get(settings.JWT_REFRESH_COOKIE)
    if raw_refresh:
        try:
            RefreshToken(raw_refresh).blacklist()
        except Exception:
            pass
    response = Response(status=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(settings.JWT_REFRESH_COOKIE, path=settings.JWT_REFRESH_COOKIE_PATH, samesite=settings.JWT_COOKIE_SAMESITE)
    return response

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_session(request):
    user = request.user
    return Response({"id": str(user.pk), "email": user.email, "first_name": user.first_name, "last_name": user.last_name, "preferred_language": user.preferred_language})

from django.core.cache import cache
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from .serializers import EmailSerializer, PasswordResetConfirmSerializer
from .tokens import reset_cooldown_key
from .tasks import send_password_reset_email

class RecoveryThrottle(AnonRateThrottle):
    scope = "recovery"

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecoveryThrottle])
def resend_activation(request):
    serializer = EmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    key = reset_cooldown_key("activation", email)
    allowed = cache.add(key, "sent", timeout=60)
    if allowed:
        user = User.objects.filter(email=email, is_active=False).first()
        if user:
            send_activation_email.delay(str(user.pk))
    return Response({"detail": _("If the account needs activation, an email will be sent.")}, status=status.HTTP_202_ACCEPTED)

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecoveryThrottle])
def request_password_reset(request):
    serializer = EmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    key = reset_cooldown_key("password-reset", email)
    if cache.add(key, "sent", timeout=60):
        user = User.objects.filter(email=email, is_active=True).first()
        if user:
            send_password_reset_email.delay(str(user.pk))
    return Response({"detail": _("If an active account uses this address, password reset instructions will be sent.")}, status=status.HTTP_202_ACCEPTED)

@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecoveryThrottle])
def confirm_password_reset(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user_id = urlsafe_base64_decode(serializer.validated_data["uid"]).decode()
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_id, is_active=True)
            token = serializer.validated_data["token"]
            if not default_token_generator.check_token(user, token):
                raise ValueError("invalid token")
            password_validation.validate_password(serializer.validated_data["password"], user=user)
            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=["password", "updated_at"])
            outstanding = OutstandingToken.objects.filter(user=user)
            blacklisted_ids = BlacklistedToken.objects.filter(token__in=outstanding).values_list("token_id", flat=True)
            for item in outstanding.exclude(pk__in=blacklisted_ids):
                BlacklistedToken.objects.get_or_create(token=item)
    except DjangoValidationError as exc:
        return Response({"detail": _("The password does not meet the requirements."), "code": "invalid_password", "fields": {"password": exc.messages}}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError, User.DoesNotExist):
        return Response({"detail": _("This password reset link is invalid, expired, or already used."), "code": "invalid_reset", "fields": {}}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": _("Password updated. Please sign in again.")})

from django.http import JsonResponse
from django.utils import timezone
from .serializers import AccountSettingsSerializer
from .tokens import read_email_change_token
from .tasks import send_email_change_verification

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def account_settings(request):
    user = request.user
    if request.method == "GET":
        return Response({"id": str(user.pk), "full_name": f"{user.first_name} {user.last_name}".strip(), "email": user.email, "pending_email": user.pending_email, "phone": user.phone, "preferred_language": user.preferred_language})
    serializer = AccountSettingsSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        if "full_name" in data:
            names = data["full_name"].split(maxsplit=1)
            user.first_name, user.last_name = names[0], names[1] if len(names) > 1 else ""
        if "phone" in data:
            user.phone = data["phone"]
        if "preferred_language" in data:
            user.preferred_language = data["preferred_language"]
        if data.get("new_email") and data["new_email"] != user.email:
            if User.objects.filter(email=data["new_email"]).exclude(pk=user.pk).exists():
                return Response({"detail": _("That email address is already in use."), "code": "email_unavailable", "fields": {"new_email": [_("That email address is already in use.")]}}, status=status.HTTP_400_BAD_REQUEST)
            user.pending_email = data["new_email"]
            transaction.on_commit(lambda: send_email_change_verification.delay(str(user.pk)))
        user.save()
    return Response({"id": str(user.pk), "full_name": f"{user.first_name} {user.last_name}".strip(), "email": user.email, "pending_email": user.pending_email, "phone": user.phone, "preferred_language": user.preferred_language})

@api_view(["POST"])
@permission_classes([AllowAny])
def confirm_email_change(request):
    try:
        payload = read_email_change_token(str(request.data.get("token", "")))
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=payload["user_id"], is_active=True)
            new_email = payload["email"]
            if not new_email or user.pending_email != new_email or User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
                raise ValueError("stale change")
            old_email = user.email
            user.email = new_email
            user.pending_email = ""
            user.save(update_fields=["email", "pending_email", "updated_at"])
            transaction.on_commit(lambda: send_mail("Your KabulCV email changed", "The login email for your KabulCV account was changed. Contact support if you did not request this.", settings.DEFAULT_FROM_EMAIL, [old_email], fail_silently=True))
    except (signing.BadSignature, signing.SignatureExpired, KeyError, ValueError, User.DoesNotExist):
        return Response({"detail": _("This email verification link is invalid, expired, or no longer current."), "code": "invalid_email_change", "fields": {}}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"detail": _("Your email address has been updated.")})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_account_data(request):
    user = request.user
    return JsonResponse({"account": {"id": str(user.pk), "name": f"{user.first_name} {user.last_name}".strip(), "email": user.email, "pending_email": user.pending_email, "phone": user.phone, "preferred_language": user.preferred_language, "created_at": user.created_at.isoformat(), "updated_at": user.updated_at.isoformat()}}, headers={"Content-Disposition": "attachment; filename=\"kabulcv-account-data.json\"", "Cache-Control": "private, no-store"})
