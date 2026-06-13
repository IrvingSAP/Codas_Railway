from django.urls import path

from apps.company import views

app_name = "company"

urlpatterns = [
    path("", views.company_list, name="list"),
    path("nueva/", views.company_create, name="create"),
    path("<int:pk>/", views.company_detail, name="detail"),
    path("<int:pk>/editar/", views.company_update, name="update"),
    path("<int:pk>/eliminar/", views.company_delete, name="delete"),
]
