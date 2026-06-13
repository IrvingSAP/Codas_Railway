from django.urls import path

from apps.maintenance_builder import views

app_name = "maintenance_builder"

urlpatterns = [
    path("", views.list_view, name="list_view"),
    path("crear/", views.create_view, name="create_view"),
    path("crear/paso-1/", views.create_view, name="wizard_step1"),
    path("crear/<int:pk>/paso-2/", views.wizard_step2, name="wizard_step2"),
    path("crear/<int:pk>/paso-3/", views.wizard_step3, name="wizard_step3"),
    path("crear/<int:pk>/paso-4/", views.wizard_step4, name="wizard_step4"),
    path("crear/<int:pk>/paso-5/", views.wizard_step5, name="wizard_step5"),
    path("crear/<int:pk>/paso-6/", views.wizard_step6, name="wizard_step6"),
    path("crear/<int:pk>/paso-7/", views.wizard_step7, name="wizard_step7"),
    path("crear/<int:pk>/paso-8/", views.wizard_step8, name="wizard_step8"),
    path("crear/<int:pk>/paso-9/", views.wizard_step9, name="wizard_step9"),
    path("<int:pk>/", views.detail_view, name="detail_view"),
    path("<int:pk>/editar/", views.update_view, name="update_view"),
]
