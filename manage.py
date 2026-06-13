#!/usr/bin/env python
"""Punto de entrada de Django para CODAS."""
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codas.settings.local")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Está instalado y activo el entorno virtual?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
