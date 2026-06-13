# CODAS — Panel de facturación (datos reales)

**Base URL:** `/panel/billing/` (nombre de URL `billing:hub`).

**Permisos (alineado con compañías):**

- **SU (superusuario):** alta, edición y baja de planes, suscripciones, contactos y pagos.
- **AC (admin de compañía):** consulta de listados y detalles filtrados a **su compañía** (suscripción, contactos y pagos asociados). Sin botones de creación/edición/eliminación.

**Requisitos:** usuario autenticado, `UserProfile` existente, tipo SU o AC (mantenedor de compañía).

---

## Orden recomendado de carga

1. **Planes** (`/panel/billing/planes/`): definir el catálogo (código único, periodo, descripción).
2. **Compañía** (módulo Compañías): la compañía debe existir **sin** suscripción previa para poder crear una nueva.
3. **Suscripción** (`/panel/billing/suscripciones/nueva/`): elegir compañía (solo las que aún no tienen fila de suscripción), plan, fechas de vigencia, estado y renovación automática. Al guardar, el modelo recalcula `integrity_signature` (HMAC).
4. **Contactos** (hasta 3 por suscripción): `/panel/billing/contactos/`.
5. **Pagos:** solo si la suscripción está **activa** o **pendiente** (`Payment.clean()`). Ruta: `/panel/billing/pagos/`.

---

## Rutas principales

| Recurso | Listado | Alta |
|---------|---------|------|
| Hub | `/panel/billing/` | — |
| Planes | `.../planes/` | `.../planes/nuevo/` |
| Suscripciones | `.../suscripciones/` | `.../suscripciones/nueva/` |
| Contactos | `.../contactos/` | `.../contactos/nuevo/` |
| Pagos | `.../pagos/` | `.../pagos/nuevo/` |

Detalle y edición: `/<recurso>/<id>/`, `/<recurso>/<id>/editar/`, eliminar: `/<recurso>/<id>/eliminar/`.

---

## Código relacionado

- Vistas: `apps/billing/views.py`
- Formularios: `apps/billing/forms.py`
- Reglas de acceso: `apps/billing/services/access.py`
- Integridad de licencia y secreto: `docs/CODAS_PROC_LLAVE_INTEGRIDAD_SUSCRIPCION.md`

---

*Última revisión: panel operativo sin modo demo.*
