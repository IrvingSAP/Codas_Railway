from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.services.email_delivery import email_delivery_user_message
from apps.security.services.actualizar_2fa import process_security_actualizar_2fa_step
from apps.security.services.email_confirmation import (
    confirm_email_on_profile,
    issue_new_email_code,
    send_email_confirmation,
    should_issue_fresh_email_code,
    verify_submitted_email_code,
)
from apps.security.services.profile_routing import is_active_for_totp_login
from apps.security.services.security_login import process_security_login_step
from apps.security.services.security_session import clear_security_flow, get_pending_user_id
from apps.security.services.totp_reset import apply_profile_2fa_reset
from apps.security.services.totp_utils import (
    build_provisioning_uri,
    generate_totp_secret,
    qr_code_png_data_uri,
    verify_totp_code,
)
from apps.userprofile.models import UserProfile

User = get_user_model()

MSG_TOTP_INVALID = "Error en validación"
MSG_EMAIL_INVALID = "Error en validación"


def _redirect_security_login() -> HttpResponse:
    return redirect("security:security_login")


def _load_pending_user_profile(request: HttpRequest):
    uid = get_pending_user_id(request)
    if uid is None:
        return (None, None, _redirect_security_login())
    try:
        user = User.objects.get(pk=uid)
        profile = user.profile
    except User.DoesNotExist:
        return (None, None, _redirect_security_login())
    except UserProfile.DoesNotExist:
        return (None, None, _redirect_security_login())
    return (user, profile, None)


def security_login(request: HttpRequest) -> HttpResponse:
    """
    Primera pantalla de acceso: usuario y contraseña.

    Contrato: CODAS_SECURITY.md (paso 1 — credenciales; usuario nuevo y activo).
    """
    if request.GET.get("cancel"):
        clear_security_flow(request)

    if request.method != "POST":
        return render(request, "security/security_login.html", {})

    result = process_security_login_step(request)
    errors = result.get("errors") or []
    redirect_url = result.get("redirect_url")
    info_message = result.get("info_message")

    if redirect_url:
        return redirect(redirect_url)

    if info_message:
        messages.info(request, info_message)

    return render(
        request,
        "security/security_login.html",
        {
            "errors": errors,
            "username": (request.POST.get("username") or "").strip(),
        },
    )


@require_http_methods(["GET", "POST"])
def security_actualizar_2fa(request: HttpRequest) -> HttpResponse:
    """Entrada alternativa para §9: credenciales y reset antes del ciclo correo + 2FA."""
    if request.method == "GET":
        return render(request, "security/security_actualizar_2fa.html", {})

    result = process_security_actualizar_2fa_step(request)
    errors = result.get("errors") or []
    redirect_url = result.get("redirect_url")
    if redirect_url:
        messages.info(
            request,
            "Se reinició el segundo factor. Valide su correo para continuar.",
        )
        return redirect(redirect_url)

    return render(
        request,
        "security/security_actualizar_2fa.html",
        {
            "errors": errors,
            "username": (request.POST.get("username") or "").strip(),
        },
    )


@require_http_methods(["GET", "POST"])
def security_email_code(request: HttpRequest) -> HttpResponse:
    """Paso 2 — Código enviado al correo (CODAS_SECURITY §2)."""
    user, profile, err_response = _load_pending_user_profile(request)
    if err_response is not None:
        return err_response

    if profile.email_confirmed and profile.tfa_verified:
        return redirect("security:security_totp")
    if profile.email_confirmed and not profile.tfa_verified:
        return redirect("security:security_totp_setup")

    if request.method == "GET":
        email_sent = True
        if should_issue_fresh_email_code(profile):
            code = issue_new_email_code(profile)
            try:
                send_email_confirmation(user=user, code=code)
            except Exception as exc:
                email_sent = False
                messages.error(request, email_delivery_user_message(exc))
        else:
            email_sent = bool((profile.email_confirm_code or "").strip())
        return render(
            request,
            "security/security_email_code.html",
            {"email": user.email, "email_sent": email_sent},
        )

    if request.POST.get("action") == "cancelar":
        clear_security_flow(request)
        return _redirect_security_login()

    if request.POST.get("action") == "reenviar":
        code = issue_new_email_code(profile)
        email_sent = True
        try:
            send_email_confirmation(user=user, code=code)
            messages.info(request, "Se envió un nuevo código al correo.")
        except Exception as exc:
            email_sent = False
            messages.error(request, email_delivery_user_message(exc))
        return render(
            request,
            "security/security_email_code.html",
            {"email": user.email, "email_sent": email_sent},
        )

    submitted = (request.POST.get("email_code") or "").strip()
    ok, reason = verify_submitted_email_code(profile, submitted)
    if ok:
        confirm_email_on_profile(profile)
        return redirect("security:security_totp_setup")

    if reason == "empty":
        errors = ["Ingrese el código recibido por correo."]
    elif reason in ("wrong", "expired", "missing"):
        errors = [MSG_EMAIL_INVALID]
    else:
        errors = [MSG_EMAIL_INVALID]

    return render(
        request,
        "security/security_email_code.html",
        {"email": user.email, "errors": errors},
    )


@require_http_methods(["GET", "POST"])
def security_totp_setup(request: HttpRequest) -> HttpResponse:
    """Paso 3 — QR y primer TOTP (usuario nuevo / intermedio, CODAS_SECURITY §3)."""
    user, profile, err_response = _load_pending_user_profile(request)
    if err_response is not None:
        return err_response

    if not profile.email_confirmed:
        return redirect("security:security_email_code")

    if profile.tfa_verified:
        clear_security_flow(request)
        messages.info(request, "El segundo factor ya estaba verificado. Inicie sesión de nuevo.")
        return _redirect_security_login()

    if request.method == "GET":
        if not (profile.totp_secret or "").strip():
            profile.totp_secret = generate_totp_secret()
            profile.save(update_fields=["totp_secret", "updated_at"])
        uri = build_provisioning_uri(secret=profile.totp_secret, account_name=user.get_username())
        qr_src = qr_code_png_data_uri(provisioning_uri=uri)
        return render(
            request,
            "security/security_totp_setup.html",
            {"qr_src": qr_src, "username": user.get_username()},
        )

    if request.POST.get("action") == "cancelar":
        clear_security_flow(request)
        return _redirect_security_login()

    code = (request.POST.get("totp_code") or "").strip()
    if not verify_totp_code(secret=profile.totp_secret or "", code=code):
        uri = build_provisioning_uri(secret=profile.totp_secret or "", account_name=user.get_username())
        qr_src = qr_code_png_data_uri(provisioning_uri=uri)
        return render(
            request,
            "security/security_totp_setup.html",
            {
                "qr_src": qr_src,
                "username": user.get_username(),
                "errors": [MSG_TOTP_INVALID],
            },
        )

    profile.tfa_verified = True
    profile.save(update_fields=["tfa_verified", "updated_at"])
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    clear_security_flow(request)
    return redirect("dashboard:home")


@require_http_methods(["GET", "POST"])
def security_totp(request: HttpRequest) -> HttpResponse:
    """Paso 3 — TOTP usuario activo; opción reset §9 (CODAS_SECURITY §8)."""
    user, profile, err_response = _load_pending_user_profile(request)
    if err_response is not None:
        return err_response

    if not is_active_for_totp_login(user, profile):
        if not profile.email_confirmed:
            return redirect("security:security_email_code")
        return redirect("security:security_totp_setup")

    if request.method == "GET":
        return render(request, "security/security_totp.html", {})

    if request.POST.get("action") == "cancelar":
        clear_security_flow(request)
        return _redirect_security_login()

    if request.POST.get("action") == "reset_2fa":
        apply_profile_2fa_reset(profile)
        messages.info(
            request,
            "Se reinició el segundo factor. Debe validar de nuevo su correo.",
        )
        return redirect("security:security_email_code")

    code = (request.POST.get("totp_code") or "").strip()
    if not verify_totp_code(secret=profile.totp_secret or "", code=code):
        return render(
            request,
            "security/security_totp.html",
            {"errors": [MSG_TOTP_INVALID]},
        )

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    clear_security_flow(request)
    return redirect("dashboard:home")


def security_cancel(request: HttpRequest) -> HttpResponse:
    clear_security_flow(request)
    return _redirect_security_login()
