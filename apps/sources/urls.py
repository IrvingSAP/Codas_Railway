from django.urls import path

from apps.sources import views

app_name = "sources"

urlpatterns = [
    path("", views.source_list, name="list"),
    path("nueva/", views.source_create, name="create"),
    path("<int:pk>/", views.source_detail, name="detail"),
    path("<int:pk>/editar/", views.source_update, name="update"),
    path("<int:pk>/eliminar/", views.source_delete, name="delete"),
]
