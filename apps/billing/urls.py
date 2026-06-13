"""Rutas de facturación bajo ``/panel/billing/``."""

from django.urls import path

from apps.billing import views

app_name = "billing"

urlpatterns = [
    path("", views.billing_hub, name="hub"),
    path("planes/", views.plan_list, name="plan_list"),
    path("planes/nuevo/", views.plan_create, name="plan_create"),
    path("planes/<int:pk>/", views.plan_detail, name="plan_detail"),
    path("planes/<int:pk>/editar/", views.plan_update, name="plan_update"),
    path("planes/<int:pk>/eliminar/", views.plan_delete, name="plan_delete"),
    path("suscripciones/", views.subscription_list, name="subscription_list"),
    path("suscripciones/nueva/", views.subscription_create, name="subscription_create"),
    path("suscripciones/<int:pk>/", views.subscription_detail, name="subscription_detail"),
    path("suscripciones/<int:pk>/editar/", views.subscription_update, name="subscription_update"),
    path(
        "suscripciones/<int:pk>/eliminar/",
        views.subscription_delete,
        name="subscription_delete",
    ),
    path("contactos/", views.subscriptioncontact_list, name="subscriptioncontact_list"),
    path("contactos/nuevo/", views.subscriptioncontact_create, name="subscriptioncontact_create"),
    path(
        "contactos/<int:pk>/",
        views.subscriptioncontact_detail,
        name="subscriptioncontact_detail",
    ),
    path(
        "contactos/<int:pk>/editar/",
        views.subscriptioncontact_update,
        name="subscriptioncontact_update",
    ),
    path(
        "contactos/<int:pk>/eliminar/",
        views.subscriptioncontact_delete,
        name="subscriptioncontact_delete",
    ),
    path("pagos/", views.payment_list, name="payment_list"),
    path("pagos/nuevo/", views.payment_create, name="payment_create"),
    path("pagos/<int:pk>/", views.payment_detail, name="payment_detail"),
    path("pagos/<int:pk>/editar/", views.payment_update, name="payment_update"),
    path("pagos/<int:pk>/eliminar/", views.payment_delete, name="payment_delete"),
]
