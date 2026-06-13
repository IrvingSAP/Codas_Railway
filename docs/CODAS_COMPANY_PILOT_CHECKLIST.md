# CODAS — Checklist piloto OperationResult (rollout por apps)

Seguimiento de la adopción del patrón **`OperationResult` + `safe_operation`** (`apps/core/services/`), sustituto del diseño DBResponse / DBUtils.safe_query.

Complementa [`CODAS_UI_MESSAGES.md`](CODAS_UI_MESSAGES.md) y [`CODAS_DATABASE.md`](CODAS_DATABASE.md) § 5 (tests automáticos).

---

## 0. Estado global del rollout

| App | Estado | Servicios | Vistas refactorizadas | Tests |
|-----|--------|-----------|----------------------|-------|
| **`apps.core`** | Hecho | `operation_result.py`, `operation_messages.py` | N/A (infraestructura) | `test_operation_result.py` |
| **`apps.company`** | **Hecho** | `company_persistence.py` | `create`, `update`, `delete` | `test_company_persistence.py`, `test_views.py` |
| **`apps.table_design`** | **Hecho** | `header_persistence.py`, `field_persistence.py` | Cabecera create/update; campo create/update/delete | `test_operation_persistence.py` |
| **`apps.sp_asistido`** | **Hecho** | `sp_persistence.py` | `definition_edit`, `definition_reopen_wizard`; wizards paso 2 y confirmación script (ADD/READ/DLT/UPD) | `test_sp_persistence.py` (+ `tests.py` existente) |
| **`apps.maintenance_builder`** | Pendiente | — | — | — |
| **`apps.userprofile`** | **Hecho** | `userprofile_persistence.py` | `create`, `update`, `delete` | `test_userprofile_persistence.py`, `test_views.py`, `test_access.py` |
| **`apps.security`** | Pendiente | — | — | — |
| **`apps.billing`** | Pendiente | — | — | — |
| **`apps.sources`** | Pendiente | — | — | — |
| **`apps.dashboard`** | Pendiente | — | — | — |

**Fuera de alcance inicial (sin cambio):** mutaciones de campos bloqueadas por reglas de negocio (`script_generated`, cabecera inactiva), atributos DB2 (`field_db2_attributes`), orden de campos (`field_move_*`), confirmación de script DDL (`header_script` POST).

---

## 1. Requisitos previos (todas las apps)

- [ ] PostgreSQL operativo y `.env` con `DATABASE_URL` o `DB_*`.
- [ ] Tests automáticos en verde (ver § 2 por app).
- [ ] Servidor local: `python manage.py runserver`.

---

## 2. Tests automáticos

### 2.1 Core (sin BD obligatoria)

```powershell
python manage.py test apps.core.tests.test_operation_result
```

### 2.2 Company (piloto 1)

```powershell
python manage.py test apps.company.tests
```

| Módulo | Qué cubre |
|--------|-----------|
| `test_company_persistence.py` | Servicios create/update/delete/get |
| `test_views.py` | Vistas POST, duplicados, permisos |

- [ ] Tests `apps.company.tests` en verde.

### 2.3 Table design (piloto 2)

```powershell
python manage.py test apps.table_design.tests.test_operation_persistence apps.table_design.tests.test_detail_table_views
```

| Módulo | Qué cubre |
|--------|-----------|
| `test_operation_persistence.py` | Cabecera create/update (script reset), campo CRUD |
| `test_detail_table_views.py` | Acceso HTTP, bloqueos de negocio, edición cabecera |

- [ ] Tests de persistencia y vistas table_design en verde.

### 2.4 Userprofile (piloto 3)

```powershell
python manage.py test apps.userprofile.tests
```

| Módulo | Qué cubre |
|--------|-----------|
| `test_userprofile_persistence.py` | Servicios create/update/delete |
| `test_views.py` | Alta POST, duplicado, formulario inválido |
| `test_access.py` | Permisos SU/AC/US en listado |
| `test_company_user_metrics.py` | Métricas US/AS por compañía |

- [ ] Tests `apps.userprofile.tests` en verde.

### 2.5 SP Asistido (piloto 4)

```powershell
python manage.py test apps.sp_asistido.tests.test_sp_persistence apps.sp_asistido.tests
```

| Módulo | Qué cubre |
|--------|-----------|
| `test_sp_persistence.py` | Borrador paso 2, edición identificación, confirmación script |
| `tests.py` | Validación ADD/READ/DLT/UPD y generadores SQL |

- [ ] Tests de persistencia y suite `apps.sp_asistido.tests` en verde.

Si el rol de BD no tiene `CREATEDB`, ver [`CODAS_DATABASE.md`](CODAS_DATABASE.md) § 5.

---

## 3. Checklist manual — `apps.company` (SU)

Ruta: **Panel → Compañías** (`/panel/companies/`).

### 3.1 Crear / editar / eliminar

| # | Acción | Resultado esperado | OK |
|---|--------|-------------------|-----|
| 1 | Nueva compañía válida | Modal éxito + detalle | [ ] |
| 2 | Nombre corto duplicado | Modal catálogo + error en campo; re-render | [ ] |
| 3 | Editar y guardar | Modal «Compañía actualizada…» | [ ] |
| 4 | Eliminar sin dependencias | Modal éxito + listado | [ ] |
| 5 | Eliminar con diseños de tabla | Modal error de negocio | [ ] |

---

## 4. Checklist manual — `apps.table_design` (AS/US con compañía)

Ruta: **Panel → Diseño de tablas** (`/panel/table-design/`).

### 4.1 Cabecera

| # | Acción | Resultado esperado | OK |
|---|--------|-------------------|-----|
| 1 | Nueva cabecera válida | Modal éxito + listado | [ ] |
| 2 | Nombre corto duplicado en compañía | Modal duplicado + error en formulario | [ ] |
| 3 | Editar cabecera (sin script) | Modal «Cabecera… actualizada» | [ ] |
| 4 | Editar cabecera con **script generado** y cambiar un campo | Guardado OK; `script_generated=False`, `script_date` vacío | [ ] |
| 5 | Cabecera **inactiva** → Editar | Redirect + modal error (sin formulario) | [ ] |

### 4.2 Campos

| # | Acción | Resultado esperado | OK |
|---|--------|-------------------|-----|
| 6 | Crear campo válido | Modal «Campo guardado…» | [ ] |
| 7 | Nombre de campo duplicado | Modal catálogo + re-render formulario | [ ] |
| 8 | Eliminar campo | Modal «Campo eliminado…» | [ ] |
| 9 | Cabecera con script → mutación campo | Bloqueo de negocio (sin OperationResult en move/DB2) | [ ] |

---

## 5. Checklist manual — `apps.userprofile` (SU / AC mantenedor)

Ruta: **Panel → Perfiles de usuario** (`/panel/userprofiles/`).

| # | Acción | Resultado esperado | OK |
|---|--------|-------------------|-----|
| 1 | Alta de perfil válida (SU) | Modal éxito + detalle | [ ] |
| 2 | Usuario duplicado | Error en campo usuario; re-render (formulario o catálogo) | [ ] |
| 3 | Editar perfil de la compañía (AC) | Modal «Perfil actualizado…» | [ ] |
| 4 | Eliminar perfil | Modal «Perfil eliminado…» + listado | [ ] |
| 5 | US sin rol mantenedor → listado | Redirect al panel + advertencia | [ ] |

---

## 6. Checklist manual — `apps.sp_asistido` (AS con compañía)

Ruta: **Panel → SP Asistido** (`/panel/sp-asistido/`).

| # | Acción | Resultado esperado | OK |
|---|--------|-------------------|-----|
| 1 | Wizard ADD paso 2 (tabla válida) | Borrador creado; mensaje de éxito del catálogo | [ ] |
| 2 | Confirmar script ADD (paso 7) | Script guardado; sin texto SQL crudo en modal de error | [ ] |
| 3 | Editar identificación en ficha | «Cambios guardados» o error de catálogo | [ ] |
| 4 | Reabrir asistente con script previo | Borrador + advertencia; sin `DatabaseError` literal | [ ] |
| 5 | Repetir confirmación en READ/DLT/UPD | Mismo patrón de mensajes | [ ] |

---

## 7. Logs (errores simulados)

- [ ] Duplicado o error de BD: detalle técnico solo en logs.
- [ ] Modal al usuario: textos del catálogo, sin SQL ni `IntegrityError` literal.

---

## 8. Cierre por fase

| Fase | Criterio | Estado |
|------|----------|--------|
| Piloto 1 — `company` | § 2.2 + § 3 | [ ] |
| Piloto 2 — `table_design` | § 2.3 + § 4 | [ ] |
| Piloto 3 — `userprofile` | § 2.4 + § 5 | [ ] |
| Piloto 4 — `sp_asistido` | § 2.5 + § 6 | [ ] |
| Rollout — `maintenance_builder`, `security`, `billing`, `sources`, `dashboard` | Ver tabla § 0 | [ ] Pendiente |

**Responsable / fecha:** _______________________

**Notas:** _______________________________________________

---

## 9. Referencias

| App | Servicios | Vistas |
|-----|-----------|--------|
| `company` | `apps/company/services/company_persistence.py` | `apps/company/views.py` |
| `table_design` | `apps/table_design/services/header_persistence.py`, `field_persistence.py` | `apps/table_design/views.py` |
| `userprofile` | `apps/userprofile/services/userprofile_persistence.py` | `apps/userprofile/views.py` |
| `sp_asistido` | `apps/sp_asistido/services/sp_persistence.py` | `views.py`, `views_*_wizard.py` |
| Catálogo | [`CODAS_UI_MESSAGES.md`](CODAS_UI_MESSAGES.md) | |

*Última revisión: may/2026 — `company`, `table_design`, `userprofile` y `sp_asistido` implementados; `maintenance_builder`, `security`, `billing`, `sources` y `dashboard` pendientes.*
