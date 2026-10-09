from django.urls import path
from .views import register, activate, login, refresh_session, logout, current_session, resend_activation, request_password_reset, confirm_password_reset, account_settings, confirm_email_change, export_account_data

urlpatterns = [
    path("register/", register, name="register"),
    path("activate/", activate, name="activate"),
    path("activation/resend/", resend_activation, name="activation-resend"),
    path("password/reset/", request_password_reset, name="password-reset-request"),
    path("password/reset/confirm/", confirm_password_reset, name="password-reset-confirm"),
    path("auth/login/", login, name="login"),
    path("auth/refresh/", refresh_session, name="refresh"),
    path("auth/logout/", logout, name="logout"),
    path("auth/me/", current_session, name="current-session"),
    path("me/settings/", account_settings, name="account-settings"),
    path("me/export/", export_account_data, name="account-export"),
    path("email/confirm/", confirm_email_change, name="email-confirm"),
]
