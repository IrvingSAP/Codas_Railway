from django.urls import path

from apps.userprofile import views

app_name = "userprofile"

urlpatterns = [
    path("", views.userprofile_list, name="list"),
    path("nuevo/", views.userprofile_create, name="create"),
    path("<int:pk>/", views.userprofile_detail, name="detail"),
    path("<int:pk>/editar/", views.userprofile_update, name="update"),
    path("<int:pk>/eliminar/", views.userprofile_delete, name="delete"),
]
