from django.shortcuts import render


def home_view(request):
    """Página de inicio (layout + contenido hero)."""
    return render(request, "core/index.html")
