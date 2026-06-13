from django.contrib.auth.views import LogoutView
from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),
    path("salir/", LogoutView.as_view(next_page="/ingresar/"), name="logout"),
]
