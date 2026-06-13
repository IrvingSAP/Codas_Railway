# CODAS — Panel de plantillas source (datos reales)

**Base URL:** `/panel/sources/` (nombre de URL `sources:list`).

**Permisos (alineado a compañía del usuario conectado):**

- **US (usuario):** acceso al módulo desde dashboard; CRUD/listado limitado a su compañía.
- **SU / AC / AS:** el módulo puede existir por ruta, pero no se muestra en navegación lateral por decisión de producto actual.

**Requisitos:** usuario autenticado, `UserProfile` existente y `profile.company` definido.

---

## Alcance funcional del módulo

`SourceTemplate` permite administrar plantillas base para generación de fuentes IBM i:

- nombre y descripción de la plantilla
- nombre de archivo (`filename`)
- tipo de fuente (`DSPF`, `SQLRPGLE`, `RPGLE`, `CLLE`)
- contenido (`source_text`)
- versión y estado
- auditoría (`created_by`, `updated_by`, timestamps)

La compañía **no se captura en pantalla**; se asigna automáticamente desde el usuario conectado.

---

## Reglas de acceso implementadas

Servicio: `apps/sources/services/access.py`

- `source_queryset_for_user(user)`: retorna solo plantillas con `company_id = request.user.profile.company_id`.
- `user_can_access_source(user, target)`: permite detalle/edición/borrado solo si la plantilla pertenece a la compañía del actor.
- Si el usuario no tiene compañía (`profile.company_id` vacío), no hay acceso al módulo.

---

## Rutas principales

| Recurso | Listado | Alta |
|---------|---------|------|
| Plantillas source | `/panel/sources/` | `/panel/sources/nueva/` |

Detalle y edición: `/panel/sources/<id>/`, `/panel/sources/<id>/editar/`, eliminar: `/panel/sources/<id>/eliminar/`.

---

## Funcionalidad del listado

- Búsqueda por `name` y `filename`.
- Filtros por `source_type` y `status`.
- Ordenamiento por:
  - nombre
  - tipo
  - estado
  - versión
- Paginación con estándar: `5, 10, 15, 20, 25`.

---

## Validaciones relevantes del modelo

Modelo: `apps/sources/models.py`

- `version >= 1`.
- Validación de extensión en `filename` según `source_type`:
  - `DSPF -> .dspf`
  - `SQLRPGLE -> .sqlrpgle`
  - `RPGLE -> .rpgle`
  - `CLLE -> .clle`
- Unicidad:
  - `company + name + version`
  - `company + filename + version` (cuando `filename` tiene valor)

---

## Código relacionado

- Modelo: `apps/sources/models.py`
- Formulario: `apps/sources/forms.py`
- Vistas: `apps/sources/views.py`
- Reglas de acceso: `apps/sources/services/access.py`
- Rutas: `apps/sources/urls.py`
- Templates:
  - `apps/sources/templates/sources/source_list.html`
  - `apps/sources/templates/sources/source_form.html`
  - `apps/sources/templates/sources/source_detail.html`
  - `apps/sources/templates/sources/source_confirm_delete.html`

---

*Última revisión: panel operativo de Sources (CRUD/list) con alcance por compañía del usuario conectado.*
