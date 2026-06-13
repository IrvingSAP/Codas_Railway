# CODAS — Reglas del módulo Generador de mantenimiento (SQLRPGLE)

Documento de reglas de negocio y de UI para el proceso de creación, edición y generación de programas de mantenimiento. Complementa el flujo acordado en el plan de producto. La implementación (modelo Django, servicios) se define cuando las pantallas estén validadas.

## 1. Alcance y principios

- El generador de mantenimiento transforma metadatos (p. ej. `HeaderTable`, `SPDefinition`, `SourceTemplate`, fuentes) en artefactos SQLRPGLE y relacionados, según se acuerde fase a fase.
- Las reglas de validación se aplican en **cliente** (UX inmediata) y en **servidor** (obligatorias, seguridad e integridad).
- Scoping por compañía: toda entidad y listado asociado debe respetar el contexto de compañía del usuario (misma política que otras apps CODAS).

## 1.1 Estándar de datatable en el flujo “Crear mantenimiento”

Todas las grillas (datatables) de este asistente deben compartir el **mismo patrón de barra de listado**, alineado con el listado CODAS de referencia (búsqueda, paginación, filtros, pie con rango y navegación).

| Elemento | Regla |
|----------|--------|
| **Registros por página** | Selector con valores fijos **10, 20, 30, 50** (no incluir otras tallas en este flujo). El valor predeterminado en UI puede ser 10. Al cambiar el tamaño, se recalcula la página 1 o se mantiene el conjunto de resultados filtrado de forma coherente. |
| **Buscar por nombre** | Campo de búsqueda **obligatorio en la barra** (etiqueta “Buscar por nombre”). Aplica a los campos de “nombre” relevantes de cada grilla: en el paso 1, nombre corto, largo y esquema de `HeaderTable`; en el paso 2, nombre del SP, descripción, esquema del SP, tabla de diseño asociada; en los pasos 7 y 8, nombre y descripción de plantilla, nombre de archivo, etc. (la implementación fija el `icontains` / criterio exacto). |
| **Filtros** | Además de la búsqueda, se presentan **filtros por columnas o dominio** acordes a la entidad (esquema, estado, tipo, script, etc.). Los valores “Todos” no restringen. Botones **Aplicar filtros** y **Limpiar** (restablecer criterios y, en Limpiar, vuelta a registros por página 10 o valor por defecto acordado). |
| **Tabla y pie** | **Obligatoriedad de selección:** pasos **1** (tabla base), **2** (READ-C), **7** (base DSPF) y **8** (base SQLRPGLE) obligatorios en su grilla; pasos **3–6** (ADD, READ-R, UPD, DLT) **opcionales** (secciones 7–10). Resto: pie con rango y paginación. |
| **Paso 9 (resumen)** | **Sin** datatable: pantalla de **solo lectura** con el resumen de lo acumulado (pasos 1–8) y acción **Generar Script**; ver sección 13. |
| **Implementación** | Misma estructura de template/partials o componente reutilizable al integrar en Django, para no duplicar marcas o clases. Los prototipos usan contenedor con clase/convención `gm-wizard-dt-toolbar` y badge “Estándar datatable” solo en Fase A. |

Prototipos pasos 1 a 9: `…-step1-…` … `…-step9-…`.

## 2. Identificador de mantenimiento (nombre / código)

| Regla | Descripción |
|--------|-------------|
| **Obligatoriedad** | El campo no puede quedar vacío (solo espacios cuenta como vacío). |
| **Longitud** | Máximo **10** caracteres. |
| **Unicidad** | No puede repetirse respecto a los demás mantenimientos de la **misma compañía** (constraint y validación en servidor; mensaje de error claro al usuario). |
| **Normalización (recomendado)** | A definir en implementación: mayúsculas, juego de caracteres permitido (A–Z, 0–9, guion bajo) para alinear nombres con convención IBM i. |
| **Reservas** | No reutilizar identificadores de objetos de sistema o conflictivos en despliegue; si aplica, documentar prefijos corporativos. |

## 3. Selección de tabla base (HeaderTable)

| Regla | Descripción |
|--------|-------------|
| **Obligatoriedad** | Debe seleccionarse **exactamente un** registro de `HeaderTable` como tabla base del mantenimiento. |
| **Origen de datos** | El listado muestra los `HeaderTable` disponibles según compañía (y permisos). No mezclar compañías. |
| **Requisitos mínimos de la fila (a validar con negocio)** | Opcionalmente se puede restringir a tablas con estado *Activo* o excluir *Inactivo*; documentar en implementación. |

## 4. Flujo del asistente "Crear mantenimiento"

Orden lógico de las pantallas (MVP y extensiones):

1. **Paso 1 — Nombre y tabla base:** identificador de mantenimiento + `HeaderTable` elegida.
2. **Paso 2 — Selección de SP para llenado de subfile:** un `SPDefinition` con operación READ en modalidad cursor (READ-C); selección **obligatoria**.
3. **Paso 3 — Selección de SP para ingreso de registro:** `SPDefinition` con operación **ADD**; selección **opcional**.
4. **Paso 4 — Selección de SP para visualizar registro:** READ + READ-R; selección **opcional** (`gm_wizard_sp_readr_id`).
5. **Paso 5 — Actualizar registro:** `operation = "UPD"`; opcional (`gm_wizard_sp_upd_id`).
6. **Paso 6 — Eliminar registro:** `operation = "DLT"`; opcional (`gm_wizard_sp_dlt_id`).
7. **Paso 7 — Selección base DSPF:** `SourceTemplate` con `source_type = "DSPF"`; selección **obligatoria** (`gm_wizard_source_dspf_id`).
8. **Paso 8 — Selección base SQLRPGLE:** `SourceTemplate` con `source_type = "SQLRPGLE"`; selección **obligatoria** (`gm_wizard_source_sqlrpgle_id`).
9. **Paso 9 — Resumen y generación:** presentación de todo lo capturado; cierre con **Generar Script** hacia el flujo de persistencia y generación (ver sección 13).

**Propagación de contexto (referencia, p. ej. sesión o borrador):** `gm_wizard_mnt`, `gm_wizard_table`, `gm_wizard_sp_readc_id` (obligatorio paso 2), `gm_wizard_source_dspf_id` (obligatorio paso 7), `gm_wizard_source_sqlrpgle_id` (obligatorio paso 8); opcionales `gm_wizard_sp_add_id`, `gm_wizard_sp_readr_id`, `gm_wizard_sp_upd_id`, `gm_wizard_sp_dlt_id`. En backend, este agregado se persiste en `apps.maintenance_builder` (tablas `MaintenanceDefinition`, `MaintenanceSpSelection`, `MaintenanceSourceSelection`, `MaintenanceStepState`, `MaintenanceScriptVersion`, `MaintenanceProcessLog`).

**Cancelar:** en cualquier paso, **Cancelar** abandona el flujo de creación hacia un destino acordado (p. ej. listado de mantenimientos) sin forzar guardado; en implementación se confirma si se descarta el borrador.

**Atrás:** permite regresar al paso anterior manteniendo lo ya capturado cuando el estado esté soportado por sesión o borrador.

## 5. Navegación y bloqueo entre pasos

| Regla | Descripción |
|--------|-------------|
| **Paso 1 → Paso 2** | No se avanza si falta un identificador de mantenimiento válido o no hay `HeaderTable` seleccionada, o si falla la unicidad del nombre. |
| **Paso 2 → Paso 3** | No se avanza si no se ha seleccionado **exactamente un** `SPDefinition` READ + READ-C (ver sección 6). |
| **Paso 3 → Paso 4** | **Siempre** se permite avanzar respecto a la grilla ADD: **0 o 1** SP. No bloquear por falta de selección. |
| **Paso 4 → Paso 5** | Avance permitido con **0 o 1** SP READ-R. |
| **Paso 5 → Paso 6** | **0 o 1** SP UPD. |
| **Paso 6 → Paso 7** | **0 o 1** SP DLT; el paso 7 no exige SP DLT, solo define la plantilla DSPF. |
| **Paso 7 → Paso 8** | Debe existir **exactamente un** `SourceTemplate` con `source_type = "DSPF"` seleccionado. Sin selección, no se avanza. |
| **Paso 8 → Paso 9** | Debe existir **exactamente un** `SourceTemplate` con `source_type = "SQLRPGLE"` seleccionado. Sin selección, no se avanza. |
| **Paso 9 — Generar Script** | Al confirmar, se ejecuta el proceso de **persistencia y generación** (sección 13.2), no un simple avance de asistente. Tras resolverse, **redirección al listado** con retroalimentación (modal) según éxito o error. |
| **Mensajes** | Bloqueos pasos **1**, **2**, **7** y **8** en su grilla. Pasos 3–6: SP opcional. |
| **Paridad cliente/servidor** | Pasos 3–6: FK opcionales o nulas (ADD, READ-R, UPD, DLT). Pasos 7 y 8: sendas FK obligatorias a `SourceTemplate` (DSPF y SQLRPGLE, compañía o global coherente con reglas de plantilla). |

## 6. Paso 2: Selección de SP para llenado de subfile

### 6.1 Título e identidad de la pantalla

- El encabezado principal de la pantalla debe identificar la acción: **«Selección de SP para llenado de Subfile»** (o redacción equivalente acordada con UX).
- Debe quedar claro que el propósito es elegir el procedimiento de lectura que alimenta el subfile (patrón READ con cursor/result set).

### 6.2 Bloque de salida (resumen del paso 1)

- En formato destacado (p. ej. etiqueta **SALIDA** o bloque de solo lectura), mostrar al menos:
  - **Nombre del mantenimiento** (el identificador capturado en el paso 1).
  - **Tabla seleccionada** (referencia legible a la `HeaderTable` elegida, p. ej. `esquema.nombre_corto` o el formato que use CODAS en listados).
- Este bloque no sustituye la persistencia: es contexto visual para el usuario. Si no hubiera datos de sesión, la implementación debe redirigir al paso 1 o mostrar aviso y enlace a completarlo.

### 6.3 Origen y filtro del listado (SPDefinition)

- La grilla lista únicamente definiciones de **SP Asistido** que cumplan **simultáneamente**:
  - `operation = "READ"` (valor del campo `operation` en `SPDefinition`)
  - `read_mode = "C"` (modalidad READ-C / cursor; en el modelo es el valor `C` de `ReadMode.CURSOR`, no el texto «READ-C» almacenado en base de datos).
- No deben mostrarse en este paso, por diseño, los READ en modalidad fila (READ-R, `read_mode = "R"`) ni operaciones ADD/UPD/DLT.
- El listado se limita a la **misma compañía** que el contexto del usuario, alineado con SP Asistido.

### 6.4 Obligatoriedad de selección

- Es **obligatorio** seleccionar **un y solo un** registro (p. ej. fila con radio) antes de continuar.
- **Siguiente** (o equivalente) no desbloquea el paso 3 mientras no haya un SP elegido. Mensaje de error accesible si se intenta avanzar sin selección.
- Al implementar, validar de nuevo en servidor el `id` del `SPDefinition` (pertenencia a compañía, `READ` + `read_mode='C'`).

### 6.5 Listado (misma regla que sección 1.1)

- Aplica el **estándar de datatable** de la sección 1.1: registros por página 10, 20, 30, 50; “Buscar por nombre”; filtros (esquema SP, estado, script) sin contradecir el criterio fijo READ + READ-C; pie con rango y Anterior / páginas / Siguiente.
- **Orden** de resultados: a definir en implementación (p. ej. actualizado descendente o nombre de SP).

### 6.6 Acciones de pie de pantalla

- **Cancelar:** visible en este paso; abandona el flujo (p. ej. vuelve al listado de mantenimientos) según sección 4.
- **Anterior (opcional pero recomendado):** regresa al paso 1 con el estado coherente.

## 7. Paso 3: Selección de SP para ingreso de registro (ADD)

### 7.1 Título e identidad de la pantalla

- El encabezado principal identifica la acción: **«Selección de SP para Ingreso de registro»** (o redacción equivalente acordada con UX).
- Debe dejarse claro que asocia (opcionalmente) el procedimiento de **alta** (INSERT) para nuevos registros.

### 7.2 Bloque de salida (Salida)

- Igual criterio que en el paso 2: mostrar en formato **SALIDA** al menos el **nombre del mantenimiento** y la **tabla seleccionada** (`HeaderTable`), reutilizando el mismo patrón visual.

### 7.3 Origen del listado (SPDefinition)

- La grilla lista solo definiciones con **`operation = "ADD"`** (SP Asistido, scope por compañía). No aplica `read_mode` (solo aplica a operación READ).

### 7.4 Selección opcional

- **No** es obligatorio marcar fila. El usuario puede pulsar **Siguiente** sin ningún `SPDefinition` ADD seleccionado.
- Conviene ofrecer acción **Quitar selección** (o equivalente) para desmarcar un radio ya elegido.
- En implementación, el FK o referencia a SP ADD en el borrador de mantenimiento es **nula** o se omite si no hay elección.

### 7.5 Listado (sección 1.1)

- Misma barra estándar: registros 10, 20, 30, 50; buscar por nombre; filtros (esquema, estado, script, etc.); pie con rango y paginación. Orden: a definir.

### 7.6 Acciones

- **Cancelar**, **Anterior** (al paso 2), **Siguiente** (sin requerir fila en la grilla; en prototipo, navega al paso 4).

## 8. Paso 4: Selección de SP para visualizar registro (READ-R)

### 8.1 Título e identidad de la pantalla

- El encabezado principal identifica la acción: **«Selección de SP para Visualizar registro»** (o redacción equivalente con UX).
- Asocia (opcionalmente) el procedimiento de lectura **READ-R** (registro único, `SELECT … INTO` / `OUT` según el contrato SP Asistido), distinto del READ-C del paso 2 (subfile/cursor).

### 8.2 Bloque de salida (Salida)

- Mismo criterio que en los pasos 2 y 3: **SALIDA** con **nombre del mantenimiento** y **tabla seleccionada** (`HeaderTable`).

### 8.3 Origen del listado (SPDefinition)

- La grilla incluye solo definiciones con **`operation = "READ"`** y **`read_mode = "R"`** (READ-R; en el modelo, `ReadMode.ROW`).
- No mezclar con READ-C ni con ADD/UPD/DLT. Se puede mostrar en la grilla (solo lectura) el **`read_row_policy`** (E/F) si aporta contexto; no forma parte del filtrado fijo de la barra de búsqueda en MVP salvo acuerdo de producto.
- Scoping por compañía, como en SP Asistido.

### 8.4 Selección opcional

- Puede avanzar **sin** fila elegida. **Quitar selección** para limpiar el radio.
- Persistencia: FK a `SPDefinition` (READ + R) nula o con id según elección; validar en servidor compañía y criterio READ + `read_mode='R'`.

### 8.5 Listado (sección 1.1)

- Registros 10, 20, 30, 50; buscar por nombre; filtros (esquema, estado, script, etc.); pie con rango y paginación; mismos botones **Aplicar filtros** / **Limpiar**.

### 8.6 Acciones

- **Cancelar**, **Anterior** (al paso 3), **Siguiente** (sin requerir selección; prototipo → paso 5).

## 9. Paso 5: Selección de SP para actualizar registro (UPD)

- **Título:** «Selección de SP para **Actualizar** registro».
- **Salida:** nombre del mantenimiento y tabla (mismo patrón).
- **Listado:** solo `SPDefinition` con `operation = "UPD"`; compañía; estándar 1.1.
- **Selección opcional;** `gm_wizard_sp_upd_id`; quitar selección; validar en servidor compañía + UPD.
- **Anterior** al paso 4. **Siguiente** sin exigir fila (prototipo → paso 6).

## 10. Paso 6: Selección de SP para eliminar registro (DLT)

- **Título:** «Selección de SP para **Eliminar** registro».
- **Salida:** nombre del mantenimiento y tabla.
- **Listado:** `operation = "DLT"`; estándar 1.1; selección opcional; `gm_wizard_sp_dlt_id`; **Anterior** al paso 5. **Siguiente** → paso 7 (prototipo).

## 11. Paso 7: Selección base DSPF

- **Título:** «**Selección Base DSPF**».
- **Salida:** nombre del mantenimiento y tabla (`HeaderTable`), mismo patrón que pasos 2–6.
- **Listado:** solo registros de **`SourceTemplate`** con **`source_type = "DSPF"`** (Pantalla DDS). Scoping: plantillas globales (`company` nulo) y de la compañía del usuario, según política de la app *sources*.
- **Estándar** sección 1.1: registros 10, 20, 30, 50; buscar por nombre; filtros acordes (p. ej. ámbito global/compañía, estado, versión); pie con rango y paginación; **Aplicar filtros** / **Limpiar**.
- **Selección obligatoria:** un único registro (radio) antes de **Siguiente**. Si no hay fila elegida, mensaje de error y no se avanza.
- **Persistencia / sesión (referencia):** `gm_wizard_source_dspf_id` con el `id` del `SourceTemplate` elegido.
- **Validación en servidor:** el id pertenece a la compañía o es plantilla global permitida; `source_type = "DSPF"`; estado y reglas de negocio adicionales si las hubiera.
- **Anterior** al paso 6. **Siguiente** → paso 8 (prototipo).

## 12. Paso 8: Selección base SQLRPGLE

- **Título:** «**Selección Base SQLRPGLE**».
- **Salida:** nombre del mantenimiento y tabla (`HeaderTable`), mismo patrón que pasos 2–7.
- **Listado:** solo registros de **`SourceTemplate`** con **`source_type = "SQLRPGLE"`** (programa SQLRPGLE). Scoping: plantillas globales y de compañía, según app *sources*.
- **Estándar** sección 1.1: registros 10, 20, 30, 50; buscar por nombre; filtros acordes (p. ej. ámbito global/compañía, estado, versión); pie con rango y paginación; **Aplicar filtros** / **Limpiar**.
- **Selección obligatoria:** un único registro (radio) antes de **Siguiente**. Si no hay fila elegida, mensaje de error y no se avanza.
- **Persistencia / sesión (referencia):** `gm_wizard_source_sqlrpgle_id` con el `id` del `SourceTemplate` elegido.
- **Validación en servidor:** el id pertenece a la compañía o es plantilla global permitida; `source_type = "SQLRPGLE"`; estado y reglas adicionales si las hubiera.
- **Anterior** al paso 7. **Siguiente** → paso 9 (prototipo).

## 13. Paso 9: Resumen y acción “Generar Script”

### 13.1 Contenido de pantalla (UI)

- **Título / identidad:** p. ej. **«Resumen del mantenimiento»**; debe dejarse claro que consolida lo indicado en los **pasos 1 a 8** antes de generar.
- **Contenido:** resumen estructurado (secciones o acordeones) con al menos: identificador y tabla (paso 1); `SPDefinition` elegidos o explícitamente “no seleccionado” para pasos opcionales; `SourceTemplate` DSPF y SQLRPGLE (nombres o referencias visibles, ids según implementación). Coherente con claves de contexto o con el registro de borrador.
- **Acciones de pie (orden recomendado):** **Cancelar** (abandona hacia el destino acordado), **Anterior** (vuelve al paso 8), **Generar Script** (acción primaria, dispara 13.2). Estilo y layout alineados con el flujo dark/Tailwind del resto de prototipos.

### 13.2 Proceso al pulsar “Generar Script” (reglas de negocio e implementación)

Orden lógico obligatorio; la implementación validará otra vez en **servidor** (integridad, compañía, existencia de FK, etc.):

1. **Persistencia en modelo de dominio:** volcar a la estructura persistida del generador (modelo aún no cerrado) todos los ids y datos del asistente: `HeaderTable`, `SPDefinition` requeridos y opcionales, `SourceTemplate` DSPF y SQLRPGLE, y metadatos de mantenimiento (compañía, usuario, fechas, según se defina). Si falla el guardado, no se trata el resultado como creado y se sigue al punto 3 en contexto de error.
2. **Generación de fuente SQLRPGLE:** a partir de las plantillas y metadatos, invocar el servicio o pipeline acordado para producir el **programa fuente SQLRPGLE** (estructura y contrato del artefacto por definir). Errores de generación se propagan hacia el punto 3.
3. **Redirección al listado y modal de resultado:** tras completar 1 y 2 con éxito, redirigir al **listado de mantenimientos** (o pantalla de destino acordada) y mostrar un **diálogo modal** con mensaje de **éxito**, p. ej. que el registro se guardó correctamente. Si falla cualquier fase, redirigir o permanecer según criterio UX, mostrando modal de **error** con texto claro, p. ej. **«Se produjo un error en el proceso»** y detalle operativo/seguridad ajustado a audiencia. No exponer excepciones crudas al usuario final. El modal debe ser **accesible** (foco, cierre, `role="dialog"` o equivalente).

*Nota (Fase A / prototipos):* el HTML demo solo **simula** el modal; no ejecuta guardado ni generación real.*

### 13.3 Persistencia aprobada (app `maintenance_builder`)

- **Cabecera:** `MaintenanceDefinition` (scope por `company`, nombre, tabla base, plantillas DSPF/SQLRPGLE, estado, metadatos de generación).
- **SP por operación:** `MaintenanceSpSelection` para READ_C/ADD/READ_R/UPD/DLT, con validación de pertenencia a compañía sobre `SPDefinition`.
- **Plantillas por rol:** `MaintenanceSourceSelection` para BASE_DSPF y BASE_SQLRPGLE, con validación de pertenencia y `source_type` sobre `SourceTemplate` (global o misma compañía).
- **Estado por paso:** `MaintenanceStepState` (snapshot JSON por paso 1..9).
- **Versionado de fuente:** `MaintenanceScriptVersion` (`script_sqlrpgle`, hash, estado, vigente).
- **Bitácora de proceso:** `MaintenanceProcessLog` para eventos de guardar/generar/error.
- **Auditoría estándar:** `created_at`, `updated_at`, `created_by`, `updated_by` en todas las tablas.
- **Enlace con diseño de tabla:** al persistir con éxito un mantenimiento sobre una `HeaderTable`, la app de mantenimiento debe actualizar **`HeaderTable.mt_associated=True`** en esa cabecera (y revertir o recalcular si se elimina el último mantenimiento asociado, cuando se defina la regla). No lo hace `apps.table_design`; ver [`CODAS_MODELS.md`](CODAS_MODELS.md) y [`CODAS_TABLE_DESIGN.md`](CODAS_TABLE_DESIGN.md) § 7.11.

## 14. Listado (Paso 1 — HeaderTable)

- Misma regla de **sección 1.1** para la grilla de `HeaderTable`.
- Búsqueda por nombre sobre nombre corto, largo y esquema; filtros adicionales: esquema, estado, tipo (física/lógica).
- **Orden** por implementación (p. ej. actualización o nombre).

## 15. Prototipos HTML (Fase A)

- Cadena: step1 → … → **step9** (resumen). Tras **Generar Script** (demo), modal y enlace al listado.

## 16. Evolución del documento

- FK obligatorias: READ-C (paso 2), plantillas `SourceTemplate` DSPF (paso 7) y SQLRPGLE (paso 8). Opcionales: ADD, READ-R, UPD, DLT (pasos 3–6). Paso 9: agregación de cierre y dispara persistencia + generación. Modelo persistido implementado en app `maintenance_builder` (migración inicial `0001_initial`).
