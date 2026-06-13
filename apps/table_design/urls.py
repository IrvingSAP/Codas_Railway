from django.urls import path

from apps.table_design import views

app_name = "table_design"

urlpatterns = [
    path("create/", views.header_table_create, name="header_create"),
    path(
        "<int:header_pk>/fields/<int:field_pk>/move-down/",
        views.field_move_down,
        name="field_move_down",
    ),
    path(
        "<int:header_pk>/fields/<int:field_pk>/move-up/",
        views.field_move_up,
        name="field_move_up",
    ),
    path(
        "<int:header_pk>/fields/<int:field_pk>/delete/",
        views.field_delete,
        name="field_delete",
    ),
    path(
        "<int:header_pk>/fields/<int:field_pk>/db2-attributes/",
        views.field_db2_attributes,
        name="field_db2_attributes",
    ),
    path(
        "<int:header_pk>/fields/<int:field_pk>/edit/",
        views.field_update,
        name="field_update",
    ),
    path(
        "<int:header_pk>/fields/create/",
        views.field_create,
        name="field_create",
    ),
    path("<int:header_pk>/fields/", views.field_list, name="field_list"),
    path("<int:header_pk>/script/", views.header_script, name="header_script"),
    path("<int:pk>/edit/", views.header_table_update, name="header_update"),
    path("<int:pk>/", views.header_table_detail, name="header_detail"),
    path("", views.header_table_list, name="header_list"),
]
