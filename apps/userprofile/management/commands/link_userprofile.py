"""
Crea la fila OneToOne en userprofile_userprofile para un usuario ya existente.

No modifica la contraseña ni los datos de auth_user. Útil tras createsuperuser
manual o restauraciones de BD donde falte el perfil.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.userprofile.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Asocia un usuario Django existente con UserProfile (get_or_create)."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--username",
            required=True,
            help="Nombre de usuario (auth_user.username).",
        )

    def handle(self, *args, **options) -> None:
        username = (options["username"] or "").strip()
        if not username:
            raise CommandError("El nombre de usuario no puede estar vacío.")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise CommandError(f"No existe usuario con username={username!r}.") from exc

        profile, created = UserProfile.objects.get_or_create(user=user)

        if user.is_superuser and profile.user_type != UserProfile.UserType.SUPERUSER:
            profile.user_type = UserProfile.UserType.SUPERUSER
            profile.save(update_fields=["user_type", "updated_at"])

        action = "creado" if created else "ya existía (sin cambios salvo tipo SU si aplica)"
        self.stdout.write(
            self.style.SUCCESS(
                f"UserProfile para {username!r}: {action}. "
                f"pk usuario={user.pk} pk perfil={profile.pk}"
            )
        )
