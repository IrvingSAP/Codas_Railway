# CODAS — Layout de interfaz (panel autenticado)

Documento de referencia para que **CRUD, listados y flujos internos** reutilicen el mismo marco visual y de plantillas que el panel principal, sin duplicar cabeceras ni menús.

**Relacionado:** flujos de acceso en [`CODAS_SECURITY.md`](CODAS_SECURITY.md); modelos en [`CODAS_MODELS.md`](CODAS_MODELS.md).

---

## 1. Alcance

| Usar este layout | No usar este layout |
|------------------|---------------------|
| Pantallas tras login, dentro del **área de aplicación** (listados, formularios, detalle, confirmaciones en contexto de panel) | Páginas **públicas** (p. ej. inicio en `apps.core` con [`core/base.html`](../apps/core/templates/core/base.html)) |
| Vistas que deben mostrar **menú lateral** y **barra superior** corporativa | **Login y wizard de seguridad** (`apps.security`: credenciales, correo, TOTP, actualizar 2FA) — mantienen su propio layout |
| Contenido que debe verse **alineado** con el dashboard actual | Respuestas mínimas (JSON, export) o pantallas sin HTML |

El layout canónico del panel es la plantilla **`dashboard_base.html`** (variante **corporativa**: barra superior a todo el ancho, sidebar ~240px, área de trabajo con ancho máximo). La **altura del viewport** y el **scroll vertical** del contenido siguen el contrato descrito en **§4.1** (evita recorte en pantallas bajas).

**Ruta en código:** [`apps/dashboard/templates/dashboard/dashboard_base.html`](../apps/dashboard/templates/dashboard/dashboard_base.html).

---

## 2. Cómo enlazar una vista nueva

1. **Autenticación:** las vistas del panel deben exigir usuario logueado (`@login_required` o equivalente) salvo decisión explícita en contra.
2. **Plantilla:** que la plantilla **extienda** el base del dashboard:

   ```django
   {% extends "dashboard/dashboard_base.html" %}
   ```

3. **Bloques habituales:**

   | Bloque | Uso |
   |--------|-----|
   | `{% block title %}` | Título de pestaña del navegador (`CODAS — …`). |
   | `{% block header_title %}` | Texto del `<h1>` en la barra superior (ej. «Compañías», «Editar usuario»). |
   | `{% block content %}` | Cuerpo principal: tablas, formularios, cards, mensajes de la vista. |
   | `{% block sidebar_nav %}` | Opcional: **sustituir** el menú lateral por defecto si la app necesita entradas propias (usar con cuidado para no duplicar lógica). |
   | `{% block extra_css %}` / `{% block extra_js %}` | Solo si la pantalla requiere CSS/JS adicional puntuales. |

4. **Contexto:** el base asume `profile` (`request.user.profile`) en plantillas que usan el menú por `user_type`; las vistas deben seguir pasando o asegurando perfil coherente con [`CODAS_MODELS.md`](CODAS_MODELS.md) (`UserProfile`).

---

## 3. Rutas y URLs

- **Entrada del panel:** `/panel/` — nombre de URL Django `dashboard:home` (app `apps.dashboard`).
- **Convención recomendada:** registrar rutas de funcionalidades **bajo el mismo prefijo** `/panel/…` (incluidas en `apps.dashboard.urls` o en apps que se incluyan bajo `path("panel/", …)`), para que bookmarking y permisos sean predecibles.
- **Cerrar sesión:** `POST` a la URL con nombre `dashboard:logout` (formulario con `{% csrf_token %}`), ya alineado con el botón del base.

Documentar en la app correspondiente (`urls.py`) cada nueva ruta del panel.

---

## 4. Estilos (Tailwind y proyecto)

- **Fuente de estilos del panel:** [`static/css/tailwind.css`](../static/css/tailwind.css), generado desde [`static/src/input.css`](../static/src/input.css).
- Tras cambiar componentes o utilidades en `input.css`, ejecutar en la raíz del proyecto:

  ```bash
  npm run build:css
  ```

- **Convención del repo:** un solo sistema de estilos (**Tailwind**); no mezclar Bootstrap u otros frameworks en las pantallas del panel salvo decisión explícita de arquitectura.

### Clases reutilizables del panel (referencia)

Definidas en `input.css` (capa `@layer components`), entre otras:

- `codas-dashboard-logo` — tamaño acotado del logo en barra superior.
- `codas-dashboard-work` — contenedor del contenido (`max-width` centrado).
- `codas-dashboard-nav-item`, `codas-dashboard-nav-item--active`, `codas-dashboard-nav-item--inactive` — ítems del menú lateral.
- `codas-dashboard-nav-icon-box`, variantes `--active` / `--inactive`.
- `codas-dashboard-nav-section` — etiqueta de sección en el menú.
- `codas-dashboard-card-metric` — cards tipo KPI (resúmenes numéricos).

Para listados y formularios CRUD, reutilizar también utilidades globales del tema (p. ej. `codas-section-title`, `codas-input`) cuando encajen; si se añaden patrones nuevos **solo del panel**, preferir prefijo `codas-dashboard-` y documentarlos aquí en una línea.

### 4.1 Contrato de altura del viewport y scroll (obligatorio en nuevas pantallas)

**Problema que evita:** si el `body` puede crecer indefinidamente (`min-height: 100vh` sin tope) y además tiene `overflow: hidden`, en pantallas bajas el contenido queda **recortado** y la barra de acciones inferior (botones «Guardar», «Volver», etc.) puede quedar **fuera del área visible** sin forma de desplazarse.

**Solución aplicada (referencia de implementación):**

| Capa | Archivo / selector | Comportamiento |
|------|-------------------|----------------|
| **HTML** | [`static/src/input.css`](../static/src/input.css) — `@layer base` → `html` | `height: 100dvh`, `max-height: 100dvh`, `min-height: 0`. Acota la altura del documento al **viewport dinámico** (`dvh`), coherente con barras del SO y del navegador. |
| **Body** | Mismo `@layer base` → `body` | `height: 100%`, `min-height: 0` (encadena con `html`). |
| **Body (clases)** | [`dashboard_base.html`](../apps/dashboard/templates/dashboard/dashboard_base.html) | `flex h-full min-h-0 flex-col overflow-hidden` — no hace scroll el body; reparte espacio en columna. |
| **Fila header + workspace** | `dashboard_base.html` — `div` bajo el `<header>` | `flex min-h-0 flex-1 flex-row overflow-hidden` — el bloque lateral + main ocupa el resto y puede **encoger** (`min-h-0`). |
| **`<main>`** | `dashboard_base.html` | `min-h-0 flex-1 overflow-y-auto overscroll-contain scroll-pb-6` + padding `px-6 pt-6 pb-10 md:px-8 md:pt-8 md:pb-12`. **Aquí** es donde el usuario debe poder hacer **scroll vertical** de todo el contenido de la vista. |

**Regla para nuevas plantillas que extienden `dashboard_base.html`:**

1. No envolver el panel en contenedores con `min-h-screen` que vuelvan a romper el tope de altura.
2. Colocar tablas, formularios largos y bloques de acciones **dentro** de `{% block content %}`; el scroll será el del `<main>` salvo que se documente otra cosa.
3. **Margen inferior en vistas largas:** en pantallas con muchas secciones (formularios de cabecera, detalle, listados con paginación), envolver el contenido del bloque en un contenedor con padding inferior extra, p. ej. `class="pb-10 md:pb-14"`, para que la última fila de botones no quede pegada al borde del área de scroll. **Referencia:** `apps/table_design/templates/table_design/header_table_form.html`, `header_table_detail.html`, `header_table_list.html`, `field_list.html`, `field_form.html`, `field_db2_attributes.html`.

Tras tocar `@layer base` en `input.css`, ejecutar `npm run build:css` y commitear [`static/css/tailwind.css`](../static/css/tailwind.css).

---

## 5. Menú lateral y estado activo

- El menú por defecto depende de `UserProfile.user_type` (`SU`, `AC`, `AS`, `US` — ver [`CODAS_MODELS.md`](CODAS_MODELS.md)).
- Hoy el ítem **«Inicio / panel»** se muestra como activo en todas las vistas que usan el base sin personalizar; cuando existan URLs reales por módulo, conviene marcar el activo según `request.path` o variable de contexto (`current_section`) para evitar confusiones.

---

## 6. Prototipos HTML (solo diseño)

Para experimentar layout sin tocar Django, existen archivos estáticos en [`static/prototypes/`](../static/prototypes/) (ver README allí). No son plantillas de producción; sirven para comparar variantes antes de volcar cambios a `dashboard_base.html` y `input.css`.

---

## 7. Mantenimiento de este documento

Actualizar **este archivo** cuando:

- cambie la estructura de `dashboard_base.html` o los bloques disponibles;
- cambie el **contrato de altura / scroll** (`html`/`body` en `@layer base`, clases de `<main>` o del contenedor flex bajo el header);
- se añadan convenciones de URL bajo `/panel/`;
- se incorporen clases `codas-dashboard-*` reutilizables en CRUD;
- se defina un patrón nuevo de **padding inferior** en vistas largas del panel.

---

*Última referencia: layout corporativo panel (`apps.dashboard`), plantilla base `dashboard_base.html`; viewport `100dvh` + scroll en `<main>` y §4.1.*
