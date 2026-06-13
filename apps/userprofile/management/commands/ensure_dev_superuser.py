"""
Crea o actualiza un superusuario de desarrollo y su UserProfile (OneToOne).

Uso típico (solo entorno local / pruebas):
  set CODAS_DEV_SUPERUSER_PASSWORD=SuClaveSegura
  python manage.py ensure_dev_superuser

Si no se define CODAS_DEV_SUPERUSER_PASSWORD, solo se usa en DEBUG con valor por defecto
documentado en --help (no usar en producción).
"""

from __future__ import annotations

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.userprofile.models import UserProfile

User = get_user_model()

DEFAULT_DEV_PASSWORD = "CodasPruebas2026!"


class Command(BaseCommand):
    help = "Crea o actualiza superusuario de pruebas y fila userprofile_userprofile homologada."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--username",
            default="codas_admin",
            help="Nombre de usuario Django (por defecto: codas_admin).",
        )
        parser.add_argument(
            "--email",
            default="admin@codas.local",
            help="Correo del usuario (auth_user.email).",
        )
        parser.add_argument(
            "--password",
            default="",
            help="Contraseña en texto plano. Si se omite, usa CODAS_DEV_SUPERUSER_PASSWORD o "
            "valor solo en DEBUG.",
        )

    def handle(self, *args, **options) -> None:
        username = (options["username"] or "").strip()
        email = (options["email"] or "").strip()
        password_opt = (options["password"] or "").strip()

        if not username:
            raise CommandError("El nombre de usuario no puede estar vacío.")

        password = password_opt or os.environ.get("CODAS_DEV_SUPERUSER_PASSWORD", "").strip()
        if not password:
            if not settings.DEBUG:
                raise CommandError(
                    "Defina --password o la variable de entorno CODAS_DEV_SUPERUSER_PASSWORD."
                )
            password = DEFAULT_DEV_PASSWORD
            self.stdout.write(
                self.style.WARNING(
                    f"Usando contraseña de desarrollo por defecto (solo DEBUG). "
                    f"Cambie CODAS_DEV_SUPERUSER_PASSWORD o use --password."
                )
            )

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        if not created:
            user.email = email or user.email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True

        user.set_password(password)
        user.save()

        profile, profile_created = UserProfile.objects.get_or_create(user=user)

        action_user = "creado" if created else "actualizado"
        action_profile = "creado" if profile_created else "ya existía (revisado)"
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario '{username}' {action_user}. "
                f"UserProfile (userprofile_userprofile) {action_profile}."
            )
        )
        self.stdout.write(f"  email: {user.email}")
        self.stdout.write(f"  pk usuario: {user.pk}  pk perfil: {profile.pk}")
