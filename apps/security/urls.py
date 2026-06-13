from django.urls import path

from apps.security import views

app_name = "security"

urlpatterns = [
    path("ingresar/", views.security_login, name="security_login"),
    path("seguridad/actualizar-2fa/", views.security_actualizar_2fa, name="security_actualizar_2fa"),
    path("seguridad/cancelar/", views.security_cancel, name="security_cancel"),
    path("seguridad/correo/", views.security_email_code, name="security_email_code"),
    path("seguridad/totp/", views.security_totp, name="security_totp"),
    path("seguridad/totp-config/", views.security_totp_setup, name="security_totp_setup"),
]
