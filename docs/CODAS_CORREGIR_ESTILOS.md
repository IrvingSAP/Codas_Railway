# CODAS — Corregir estilos (Tailwind / estáticos)

Guía breve y **checklist** para cuando los cambios de clases en plantillas **no se vean** en el navegador (texto “plano”, pastillas sin fondo, colores que no coinciden con el prototipo), aunque se haga F5 o se reinicie el servidor.

---

## 1. Causas habituales

| Causa | Qué pasa | Prioridad |
|--------|-----------|-----------|
| **CSS de Tailwind no regenerado** | Las utilidades nuevas (p. ej. `bg-slate-700/60`, `bg-violet-500/15`) **no existen** en `static/css/tailwind.css` hasta compilar. El HTML lleva la clase pero el navegador no aplica reglas. | Muy frecuente |
| **`STATIC_URL` relativo** (`"static/"` sin `/` inicial) | El navegador puede resolver `static/css/tailwind.css` **respecto a la URL actual** (p. ej. `/panel/table-design/`) y pedir una ruta incorrecta o una copia en caché distinta. | Frecuente en panel |
| **Caché del navegador** | Sigue sirviendo un `tailwind.css` antiguo. | Ocasional |

---

## 2. Checklist (orden recomendado)

1. **Confirmar `STATIC_URL` y `MEDIA_URL`**
   - En `codas/settings/base.py` deben ser rutas **absolutas desde la raíz del sitio**:
     - `STATIC_URL = "/static/"`
     - `MEDIA_URL = "/media/"`
   - Evitar `STATIC_URL = "static/"` (sin barra inicial) en proyectos con URLs bajo prefijos (`/panel/...`).

2. **Regenerar el bundle de Tailwind**
   - Desde la **raíz del repo** (donde está `package.json`):
     ```bash
     npm run build:css
     ```
   - Equivale a: `tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css`
   - En desarrollo continuo, preferir:
     ```bash
     npm run watch:css
     ```
   - Tras **cualquier cambio** de clases utilitarias en `.html` que no estén ya cubiertas por `static/src/input.css`, hay que compilar o el CSS seguirá incompleto.

3. **Comprobar que las clases están en el CSS generado** (opcional)
   - Buscar en `static/css/tailwind.css` una utilidad que acabas de añadir en la plantilla (p. ej. `bg-violet-500` o el nombre de una clase componente `codas-header-...`).
   - Si **no aparece**, el escaneo no la incluyó o falta el paso 2.

4. **Patrón robusto: componentes en `input.css`**
   - Para piezas de UI críticas (pastillas de tablas, badges), definir clases en `@layer components { ... }` con **`@apply`** de las utilidades Tailwind necesarias.
   - Referencia implementada: `static/src/input.css` — bloque *TableDesign — listado de cabeceras* (`codas-header-type-pill--physical`, `codas-header-status-pill--active`, etc.).
   - La plantilla usa **esas clases** en lugar de largas cadenas solo en HTML: así el compilador **siempre** incluye esas reglas al procesar `input.css`, aunque el `@source` de plantillas falle o quede desactualizado.

5. **Recordatorio en el propio `input.css`**
   - Tras `@source` hay un comentario que indica ejecutar `npm run build:css` cuando se cambien utilidades en HTML.

6. **Navegador**
   - Recarga forzada: `Ctrl+Shift+R` (o equivalente).
   - Si hay proxy/CDN delante de estáticos en producción, **invalidar caché** o versionar el nombre del asset si aplica.

7. **Reiniciar `runserver`** (solo si se cambió `settings` o rutas de estáticos; **no** sustituye el paso 2).

---

## 3. Caso concreto resuelto (TableDesign · listado cabeceras)

- **Síntoma:** Columna **Tipo** (“Física”) se veía como texto plano; **Modelo** sí mostraba contorno porque otras utilidades ya estaban en un bundle previo o el contraste era distinto.
- **Acciones tomadas:**
  - Ajuste de `STATIC_URL` / `MEDIA_URL` en `codas/settings/base.py`.
  - Clases componente `codas-header-*` en `static/src/input.css` y uso en `apps/table_design/templates/table_design/header_table_list.html`.
  - Ejecución de `npm run build:css`.

---

## 4. Referencias en el repo

| Recurso | Ruta |
|---------|------|
| Entrada Tailwind / `@source` / componentes | [`static/src/input.css`](../static/src/input.css) |
| CSS generado (no editar a mano) | [`static/css/tailwind.css`](../static/css/tailwind.css) |
| Scripts npm | [`package.json`](../package.json) — `build:css`, `watch:css` |
| Settings estáticos | [`codas/settings/base.py`](../codas/settings/base.py) |

---

*Documento de apoyo operativo — mantener alineado con la forma real de trabajar del equipo (build de CSS, despliegue de estáticos).*
