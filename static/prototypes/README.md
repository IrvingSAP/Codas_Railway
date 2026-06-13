# Prototipos de layout — panel CODAS

Archivos HTML estáticos para comparar tres variantes de diseño **antes** de aplicar cambios en `apps/dashboard/templates/`.

## Archivos

| Archivo | Variante |
|---------|----------|
| `dashboard-demo1-corporativo.html` | Opción 1 — corporativa (topbar + sidebar 240px + barra activa) |
| `dashboard-demo2-saas.html` | Opción 2 — compacta tipo SaaS + menú de cuenta |
| `dashboard-demo3-operativo.html` | Opción 3 — buscador en topbar + sidebar por secciones |

Cada demo incluye enlaces en la parte superior para saltar entre Demo 1, 2 y 3.

## Cómo abrirlos

1. **Doble clic** en el `.html` (el navegador usará `file://`). Hace falta **conexión a Internet** para cargar Tailwind desde el CDN.
2. Con **Django** en marcha (`runserver`), opcionalmente:  
   `http://127.0.0.1:8000/static/prototypes/dashboard-demo1-corporativo.html`  
   (y análogos para demo2 y demo3).

## Prototipos CRUD — Compañías (`Company`)

Pantallas de revisión antes de implementar el CRUD en Django, alineadas al layout corporativo y a [`docs/CODAS_UI_LAYOUT.md`](../../docs/CODAS_UI_LAYOUT.md).

| Archivo | Contenido |
|---------|-----------|
| [`company-crud-demo-list.html`](company-crud-demo-list.html) | Listado en tabla, botón «Nueva compañía», acciones Ver / Editar / Eliminar |
| [`company-crud-demo-form.html`](company-crud-demo-form.html) | Formulario alta/edición con campos del modelo `Company` |
| [`company-crud-demo-delete.html`](company-crud-demo-delete.html) | Confirmación de borrado |

El menú lateral muestra **Compañías** como ítem activo (misma idea que el enlace «Compañías» en `dashboard_base.html`).

## Prototipos CRUD — Perfiles (`UserProfile`)

Pantallas alineadas a [`docs/CODAS_MODELS.md`](../../docs/CODAS_MODELS.md) y al layout de [`docs/CODAS_UI_LAYOUT.md`](../../docs/CODAS_UI_LAYOUT.md).

| Archivo | Contenido |
|---------|-----------|
| [`userprofile-crud-demo-list.html`](userprofile-crud-demo-list.html) | Listado, búsqueda (placeholder), acciones Ver / Editar / Eliminar |
| [`userprofile-crud-demo-detail.html`](userprofile-crud-demo-detail.html) | Detalle (lectura) con bloque seguridad/auditoría |
| [`userprofile-crud-demo-form.html`](userprofile-crud-demo-form.html) | Alta/edición: compañía, contacto, tipo, estado |
| [`userprofile-crud-demo-delete.html`](userprofile-crud-demo-delete.html) | Confirmación de borrado del perfil |

El menú lateral marca **Perfiles de usuario** como ítem activo.

## Prototipo Django — TableDesign (`models.py` de referencia)

| Archivo | Contenido |
|---------|-----------|
| [`table_design_models.py`](table_design_models.py) | Referencia alineada con la app real **`apps.table_design`** ([`models.py`](../../apps/table_design/models.py)) y migración [`0001_initial`](../../apps/table_design/migrations/0001_initial.py). |

## Prototipo CRUD — Diseño de tablas (`HeaderTable`, paso 1)

Pantalla de listado detallada antes de implementar vistas Django; alineada a campos de cabecera en `apps.table_design.models.HeaderTable`.

| Archivo | Contenido |
|---------|-----------|
| [`table-design-header-list-demo.html`](table-design-header-list-demo.html) | Listado: KPIs, filtros, tabla ancha sin columna compañía (ámbito = `company_id` del usuario), columnas nombre / librería / llave / script / campos / acciones; paginación demo. Implementación: ruta panel `http://…/panel/table-design/` (`table_design:header_list`), acceso **AS** y **US** con compañía. |

## Prototipo — Campos de diseño (`DetailTable`)

Pantalla de revisión alineada a [`apps/table_design/templates/table_design/header_table_list.html`](../../apps/table_design/templates/table_design/header_table_list.html) (colores Tailwind: `codas-blue-dark`, `codas-blue-accent`, tarjetas `rounded-xl border border-white/10 bg-slate-900/50`, tabla con `divide-white/5`).

| Archivo | Contenido |
|---------|-------------|
| [`detail_table/field_list_demo.html`](detail_table/field_list_demo.html) | Cabecera en solo lectura (KPIs compactos), formulario alta de campo, tabla de filas con acciones Editar / Eliminar / ↑ / ↓; JS mínimo para tipo DB2 (longitud / decimales / orden de llave). Enlace **Campos** desde [`table-design-header-list-demo.html`](table-design-header-list-demo.html). |

## Nota

Los estilos usan **Tailwind CDN** solo para prototipado; el proyecto real sigue usando `static/src/input.css` y `npm run build:css`.
