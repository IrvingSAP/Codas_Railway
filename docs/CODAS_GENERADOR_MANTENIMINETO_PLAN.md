# CODAS_GENERADOR_MANTENIMINETO_PLAN

Documento de planificación para el **Generador de Mantenimiento SQLRPGLE** en CODAS, tomando como base los modelos actuales definidos en `docs/CODAS_MODELS.md`.

## 1) Objetivo del módulo

Construir un proceso asistido que permita **crear, editar, visualizar, regenerar y versionar** mantenimientos corporativos, generando artefactos SQLRPGLE de forma estandarizada.

El enfoque del proceso será:

1. **Primero pantallas (UX y flujo real de trabajo).**
2. **Luego diseño de modelo de datos.**
3. **Después programación y generación de script.**

## 2) Función y propósito

El generador de mantenimiento sirve para:

- Automatizar generación de programas corporativos.
- Estandarizar estructura técnica y reglas de construcción.
- Reducir tiempos de desarrollo.
- Centralizar conocimiento técnico en un motor único.
- Permitir mantenimiento evolutivo por regeneración controlada.

## 3) Base funcional y técnica a reutilizar

### Referencias de diseño

- `apps/sp_asistido/templates/sp_asistido/definition_list.html` como estándar visual para listados (filtros, búsqueda, cantidad por página, acciones).

### Referencias de datos

- `table_design` para metadatos de tabla/campos.
- `sp_asistido` para SP disponibles.
- `sources` para registros/plantillas fuente.

Fuente principal: `docs/CODAS_MODELS.md`.

## 4) Alcance funcional MVP (acordado)

### 4.1 Listado principal de mantenimientos

Pantalla de entrada del módulo con:

- Grid/listado de mantenimientos.
- Búsqueda por texto.
- Filtros.
- Cantidad de registros por página.
- Acciones por fila: **Editar** y **Ver**.
- Acción superior: **Crear**.

Estándar visual: tomar como base `definition_list.html` de `sp_asistido`.

### 4.2 Flujo Crear (wizard de 5 pantallas)

#### Paso 1 — Nombre del mantenimiento

- Captura de nombre corto/largo (según convención a definir en modelo).

#### Paso 2 — Selección de SP

- Listado de SP disponibles de `sp_asistido`.
- Con estándar de listado: filtros, búsqueda, cantidad por página.

#### Paso 3 — Selección de registros fuente

- Listado de registros disponibles en `sources`.
- Con estándar de listado: filtros, búsqueda, cantidad por página.

#### Paso 4 — Resumen previo

- Mostrar resumen de datos capturados.
- Acción principal: **Generar script**.

#### Paso 5 — Resultado final

- Mostrar resumen clave del mantenimiento.
- Mostrar script generado (vista previa).

### 4.3 Flujo Editar

- Similar al flujo Crear.
- Permite navegar entre pasos, ajustar datos y regenerar script.

### 4.4 Flujo Ver

- Pantalla de solo lectura con:
  - resumen de datos clave,
  - script generado vigente.

### 4.5 Generación MVP

- Generación inicial de artefacto:
  - **SQLRPGLE de mantenimiento**.
- Incluye:
  - vista previa,
  - versionado,
  - regeneración.

## 5) Plan por fases (orden de implementación)

## Fase A — Definición de pantallas (obligatorio primero)

Objetivo: cerrar UX y navegación completa antes de tocar modelo.

Entregables:

- Mapa de pantallas y navegación.
- Estructura visual del listado principal.
- Estructura de wizard Crear (pasos 1 a 5).
- Estructura de Editar y Ver.
- Definición de campos por pantalla y validaciones UI.

## Fase B — Modelo de datos (después de UX)

Objetivo: diseñar entidades cuando ya esté claro qué captura cada pantalla.

Lineamientos:

- Basarse en `CODAS_MODELS`.
- Reutilizar patrón de auditoría.
- Reutilizar scope por compañía.
- Incluir soporte de versionado de script.

Entregables:

- Diagrama de entidades del módulo.
- Campos mínimos por entidad.
- Relaciones con `sp_asistido` y `sources`.
- Reglas de estado y versionado.

Estado actual:

- App Django creada: `apps.maintenance_builder`.
- Modelo inicial implementado y migrado (`0001_initial`) con:
  - `MaintenanceDefinition`
  - `MaintenanceSpSelection`
  - `MaintenanceSourceSelection`
  - `MaintenanceStepState`
  - `MaintenanceScriptVersion`
  - `MaintenanceProcessLog`
- Auditoría estándar en todas las tablas: `created_at`, `updated_at`, `created_by`, `updated_by`.
- Scope por compañía en cabecera (`MaintenanceDefinition.company`) y validaciones de pertenencia para relaciones a `SPDefinition` y `SourceTemplate`.

## Fase C — Programación (al final)

Objetivo: implementar backend y generación solo con UX y modelo aprobados.

Subfases:

1. Vistas/listados y filtros.
2. Wizard Crear/Editar paso a paso.
3. Vista Ver.
4. Servicio de generación SQLRPGLE.
5. Versionado y regeneración.
6. Pruebas y ajustes.

## 6) Reglas funcionales iniciales del MVP

- No iniciar programación sin validar pantallas.
- No cerrar modelo sin validar flujo completo de pantallas.
- El script generado debe quedar asociado a una versión.
- Editar puede regenerar y crear nueva versión.
- Ver siempre muestra versión vigente y datos clave.

## 7) Riesgos y mitigaciones

- Riesgo: implementar modelo antes de cerrar UX.
  - Mitigación: respetar orden UX -> modelo -> programación.
- Riesgo: inconsistencias entre SP/sources seleccionados y generación.
  - Mitigación: validaciones de integridad en wizard antes de generar.
- Riesgo: sobreconsumo de cambios sin valor.
  - Mitigación: entregas por fase aprobada (no avanzar sin visto bueno).

## 8) Entregables del MVP

- Listado funcional de mantenimientos (con filtros y acciones).
- Wizard Crear de 9 pasos funcional.
- Flujo Editar funcional.
- Flujo Ver funcional.
- Generación SQLRPGLE con vista previa.
- Versionado y regeneración básica.

## 9) Criterio de avance entre fases

- Fase A -> B: pantallas validadas por negocio.
- Fase B -> C: modelo validado con casos de uso del wizard.
- Cierre MVP: generación + edición + visualización + versionado operativo.

Seguimiento:

- Fase B completada a nivel de estructura y migraciones.
- Fase C inicia con vistas/servicios sobre `maintenance_builder`.

## 10) Detalle Fase A — Pantalla por pantalla

Esta sección define el diseño funcional exacto de pantallas para validar UX antes de diseñar modelo y programación.

### A.0 Convenciones UI comunes (todas las pantallas)

- Base visual: `sp_asistido/definition_list.html`.
- Componentes comunes:
  - barra de búsqueda (`q`),
  - filtros (select),
  - paginación,
  - selector de cantidad por página (`per_page`),
  - acciones por fila.
- Campos de búsqueda/filtro siempre procesados con `trim`.
- Botones principales:
  - primario (acción principal),
  - secundario (volver/cancelar),
  - enlace contextual (detalle/editar/ver).

### A.1 Pantalla Listado de mantenimientos

Objetivo: visualizar mantenimientos existentes y acceder a Crear, Editar, Ver.

Campos y controles:

- `q` (search, opcional): busca por nombre corto, nombre largo, tabla, SP principal.
- `status` (select, opcional): `Borrador`, `Generado`, `Inactivo`.
- `table` (select, opcional): tabla de diseño asociada.
- `ordering` (select): por actualizado, nombre, estado.
- `per_page` (select): `10`, `15`, `25`, `50`.
- Botón `Crear mantenimiento`.
- Acciones por fila:
  - `Editar`
  - `Ver`

Columnas sugeridas del grid:

- Nombre mantenimiento (corto y largo).
- Tabla asociada.
- SP(s) vinculados.
- Estado.
- Fecha actualización.
- Script generado (Sí/No).
- Acciones.

Validaciones:

- `per_page` solo valores permitidos.
- `ordering` solo claves permitidas.
- `table` debe existir dentro del scope de compañía.
- Si filtros inválidos -> fallback a defaults, sin error bloqueante.

### A.2 Pantalla Crear — Paso 1 (Nombre del mantenimiento)

Objetivo: capturar identificación del mantenimiento.

Campos:

- `maintenance_name_short` (texto, requerido, mayúsculas sugeridas).
- `maintenance_name_long` (texto, requerido).
- `maintenance_comment` (texto, opcional).
- `maintenance_type` (select, requerido; default `SQLRPGLE` para MVP).

Validaciones:

- `maintenance_name_short` requerido.
- longitud recomendada `3..10`.
- patrón recomendado: `A-Z`, `0-9`, `_`.
- unicidad por compañía (si ya existe, no avanza).
- `maintenance_name_long` requerido.
- longitud recomendada `5..50`.
- `maintenance_comment` máximo `200`.

Navegación:

- `Siguiente` -> Paso 2.
- `Cancelar` -> Listado.

### A.3 Pantalla Crear — Paso 2 (Selección de SP de sp_asistido)

Objetivo: seleccionar SP disponibles para el mantenimiento.

Controles de listado:

- `q` (busca por nombre SP, operación, tabla).
- `operation` (filtro): `ADD`, `UPD`, `DLT`, `READ`.
- `table` (filtro por tabla diseño del SP).
- `status` (filtro): `Borrador`, `Activo`, `Inactivo`.
- `per_page`.

Grid de SP disponibles:

- checkbox/radio de selección por fila.
- columnas: esquema, nombre corto, operación, tabla, estado, fecha.
- soporte multi-selección para MVP (recomendado), mínimo 1 selección.

Validaciones:

- debe seleccionar al menos 1 SP.
- cada SP seleccionado debe pertenecer a la misma compañía.
- si se define regla por acción (futuro), validar compatibilidad.

Navegación:

- `Anterior` -> Paso 1.
- `Siguiente` -> Paso 3.

### A.4 Pantalla Crear — Paso 3 (Selección de sources)

Objetivo: seleccionar registros fuente desde app `sources`.

Controles de listado:

- `q` (nombre/archivo/versión).
- `source_type` (filtro): `SQLRPGLE`, `RPGLE`, `CLLE`, `DSPF`.
- `status` (filtro): `Activo`, `Inactivo`.
- `per_page`.

Grid de source templates:

- checkbox/radio por fila.
- columnas: nombre, tipo, archivo, versión, estado, actualizado.
- selección múltiple permitida (mínimo 1).

Validaciones:

- mínimo 1 source seleccionado.
- todos los sources dentro del scope de compañía del usuario.
- en MVP SQLRPGLE: al menos un template tipo `SQLRPGLE` o regla equivalente de fallback.

Navegación:

- `Anterior` -> Paso 2.
- `Siguiente` -> Paso 4.

### A.5 Pantalla Crear — Paso 4 (Resumen + generar script)

Objetivo: confirmar datos antes de generar.

Secciones visibles:

- Resumen identificación (paso 1).
- Resumen SP seleccionados (paso 2).
- Resumen sources seleccionados (paso 3).
- Opciones de generación:
  - `generate_sqlrpgle` (checkbox, requerido activo en MVP).

Acciones:

- `Generar script`.
- `Anterior`.

Validaciones:

- consistencia mínima de datos:
  - nombre válido,
  - al menos 1 SP,
  - al menos 1 source.
- si falla validación, no genera y muestra errores por sección.

Navegación:

- `Generar script` exitoso -> Paso 5.

### A.6 Pantalla Crear — Paso 5 (Resultado final)

Objetivo: mostrar resultado generado y datos clave.

Secciones:

- resumen del mantenimiento.
- resumen de SP/source usados.
- bloque de script generado (solo lectura, con copy).
- metadata de versión:
  - versión,
  - fecha,
  - usuario,
  - hash/resumen.

Acciones:

- `Finalizar` -> Listado.
- `Editar mantenimiento` -> flujo Editar.
- `Regenerar` (si aplica en MVP o siguiente iteración).

Validaciones:

- script no vacío.
- versión vigente marcada.

### A.7 Pantalla Editar (flujo)

Objetivo: permitir ajustes y regeneración sin crear nuevo mantenimiento desde cero.

Comportamiento:

- reutiliza pasos 1 a 5 con datos precargados.
- permite moverse entre pasos.
- al confirmar generación:
  - crea nueva versión,
  - conserva historial.

Validaciones:

- mismas de Crear por paso.
- control de concurrencia básico:
  - si cambió estado relevante entre carga y guardar, mostrar aviso y recargar.

### A.8 Pantalla Ver (solo lectura)

Objetivo: visualizar información clave y script vigente.

Secciones:

- identificación del mantenimiento.
- SP asociados.
- sources asociados.
- versión vigente del script.
- historial de versiones (lista simple).

Acciones:

- `Volver al listado`.
- `Ir a editar`.

Validaciones:

- acceso por compañía (anti-IDOR).
- si no existe o no pertenece al scope -> `404`.

