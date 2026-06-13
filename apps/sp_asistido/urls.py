from django.urls import path

from apps.sp_asistido import (
    views,
    views_add_wizard,
    views_dlt_wizard,
    views_read_wizard,
    views_upd_wizard,
)

app_name = "sp_asistido"

urlpatterns = [
    path("", views.definition_list, name="list"),
    path("export/csv/", views.definition_list_export_csv, name="list_export_csv"),
    path("wizard/cancel/<str:flow>/", views.wizard_cancel, name="wizard_cancel"),
    # Rutas ADD antes que `nuevo/<operation>/` para no capturar "add" como operación.
    path("nuevo/add/", views_add_wizard.add_wizard_step1, name="add_step1"),
    path("nuevo/add/tabla/", views_add_wizard.add_wizard_step2, name="add_step2"),
    path(
        "nuevo/add/<int:definition_id>/paso/<int:step>/",
        views_add_wizard.add_wizard_step_detail,
        name="add_step",
    ),
    path("nuevo/dlt/", views_dlt_wizard.dlt_wizard_step1, name="dlt_step1"),
    path("nuevo/dlt/tabla/", views_dlt_wizard.dlt_wizard_step2, name="dlt_step2"),
    path(
        "nuevo/dlt/<int:definition_id>/paso/<int:step>/",
        views_dlt_wizard.dlt_wizard_step_detail,
        name="dlt_step",
    ),
    path("nuevo/upd/", views_upd_wizard.upd_wizard_step1, name="upd_step1"),
    path("nuevo/upd/tabla/", views_upd_wizard.upd_wizard_step2, name="upd_step2"),
    path(
        "nuevo/upd/<int:definition_id>/paso/<int:step>/",
        views_upd_wizard.upd_wizard_step_detail,
        name="upd_step",
    ),
    path("nuevo/read/", views_read_wizard.read_wizard_step1, name="read_step1"),
    path("nuevo/read/tabla/", views_read_wizard.read_wizard_step2, name="read_step2"),
    path(
        "nuevo/read/<int:definition_id>/paso/<int:step>/",
        views_read_wizard.read_wizard_step_detail,
        name="read_step",
    ),
    path("<int:pk>/reabrir/", views.definition_reopen_wizard, name="reopen"),
    path("<int:pk>/editar/", views.definition_edit, name="edit"),
    path("<int:pk>/", views.definition_detail, name="detail"),
    path("nuevo/<str:operation>/", views.wizard_redirect, name="wizard_start"),
]
