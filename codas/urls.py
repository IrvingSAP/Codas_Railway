from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("panel/companies/", include("apps.company.urls")),
    path("panel/billing/", include("apps.billing.urls")),
    path("panel/sources/", include("apps.sources.urls")),
    path("panel/table-design/", include("apps.table_design.urls")),
    path("panel/sp-asistido/", include("apps.sp_asistido.urls")),
    path("panel/generador-mantenimiento/", include("apps.maintenance_builder.urls")),
    path("panel/userprofiles/", include("apps.userprofile.urls")),
    path("panel/", include("apps.dashboard.urls")),
    path("", include("apps.security.urls")),
    # path("", include("apps.spworkflow.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
