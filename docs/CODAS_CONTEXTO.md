# CODAS — Contexto del desarrollo

Documento vivo: amplíalo cuando cambien requisitos, alcance o decisiones. Es la **fuente de verdad** para alinear criterio de producto y dominio (no sustituye a `.cursorrules`, que cubre estándares técnicos).

---

## 1. Resumen ejecutivo

**CODAS** es una plataforma empresarial para **IBM i (AS/400 – iSeries)** pensada para **estandarizar, automatizar y acelerar** el desarrollo de componentes críticos en entornos corporativos: **tablas**, **store procedures** y **mantenimientos** empresariales.

Combina:

- Arquitectura moderna (**Python + Django**)
- Diseño corporativo profesional (UI actual: Tailwind, tema oscuro)
- Automatización avanzada (wizards, generación de artefactos)
- **Generación de artefactos listos para producción** en IBM i

CODAS no se concibe solo como un generador puntual, sino como un **marco de trabajo** para construir sistemas empresariales de forma **rápida, segura y estandarizada** sobre IBM i.

---

## 2. Qué hace CODAS (tres pilares)

### 2.1 Diseño de tablas BD2 para IBM i

- Definición de estructuras de tablas de forma **visual y estandarizada**
- Generación de **scripts SQL** ejecutables en IBM i
- Control de **tipos de datos**, claves, relaciones y metadatos
- **Repositorio corporativo** de estructuras (visión de producto; concretar modelo de datos y persistencia según **Fase 2** del roadmap, sección 7)

### 2.2 Generación de store procedures

- Wizards para SP de tipo **SELECT, INSERT, UPDATE, DELETE**
- **Validación paso a paso** y generación del script final vía **servicios** (alineado con la arquitectura del repo)
- **Documentación integrada** en el flujo
- **Control de versiones y auditoría** como objetivo de producto (definir alcance por fases)

### 2.3 Generación de mantenimientos empresariales

- **CRUD** coherentes con los modelos definidos
- **Estructura estandarizada** entre aplicaciones
- **Plantillas corporativas** (base en `apps.core` y extensiones por app)
- Integración prevista con **seguridad, roles y permisos**
- Entregables orientados a **producción** en entornos corporativos

---

## 3. Para qué sirve (valor para la empresa)

| Objetivo | Cómo ayuda CODAS |
|----------|-------------------|
| Desarrollar más rápido | Reduce trabajo manual repetitivo; wizards acotan el esfuerzo |
| Estandarizar la arquitectura | Mismos patrones para tablas, SP y mantenimientos |
| Reducir errores | Validación en cada paso del wizard |
| Aumentar productividad del equipo | Un solo lugar para desarrolladores, analistas y arquitectos |
| Control y trazabilidad | Documentación y auditoría por artefacto (según se implemente) |
| Modernizar el desarrollo en IBM i | Herramientas actuales sin abandonar la plataforma |

---

## 4. Quién usa CODAS

Pensado para:

- Arquitectos de software
- Desarrolladores IBM i
- Equipos de DBA
- Equipos de automatización
- Empresas con **sistemas core en AS/400**
- Organizaciones que priorizan **estandarización y velocidad**

---

## 5. Visión del proyecto

Convertir a CODAS en la **plataforma central** de diseño, generación y mantenimiento de artefactos empresariales para IBM i, con:

- Wizards inteligentes y generación automática de código/SQL
- **UI corporativa moderna**
- Integración con **seguridad y auditoría**
- **Módulos escalables** y arquitectura **modular y profesional**

En síntesis: **la evolución moderna del desarrollo empresarial sobre IBM i**, manteniendo el stack y convenciones acordadas en este repositorio.

---

## 6. Decisiones técnicas ya tomadas en este repositorio

| Tema | Decisión |
|------|----------|
| Backend | **Django 6.x**, Python **3.12+**, dependencias solo en **`.venv`** y `requirements.txt`. |
| Frontend | **HTML renderizado en servidor** como eje principal (sin API REST como capa central del producto en la decisión actual). |
| Estilos | **Tailwind CSS** (`static/src/input.css`); no mezclar con Bootstrap en el mismo front. |
| Marca visual | Tema **oscuro**; tokens corporativos (p. ej. `#0A1A2F`, `#1E90FF`). |
| App de layout | **`apps.core`**: plantillas base, landing, componentes bajo `templates/core/`. |
| SP Asistido (panel) | App **`apps.sp_asistido`**: definiciones SP (READ/ADD/UPD/DLT) con listado, export CSV, wizards en sesión (TTL, cancelación), detalle/edición/reabrir, **404** por recurso fuera de compañía, mensajes vía `ui_messages`, vista previa con **copiar / descargar .sql**, generación SQL con calificación alineable a `table_design` (`sql_qualification`), pruebas en `apps/sp_asistido/tests.py`. Ruta panel **`/panel/sp-asistido/`**. Normativa y flujos: [`CODAS_SP_ASISTIDO.md`](CODAS_SP_ASISTIDO.md); modelos: [`CODAS_MODELS.md`](CODAS_MODELS.md). |
| Lógica de negocio | **`services/`** por app; generación de scripts SQL en servicios, no en plantillas. |
| Wizards | Pasos claros, estado en **sesión**, validación por paso. |
| Settings Django | Paquete **`codas/settings/`**: **`base.py`** (común + logging), **`local.py`** (desarrollo), **`production.py`** (producción). Solo **local** y **production** (sin entorno `qa` separado por ahora). |
| Variables de entorno | Carga con **`python-dotenv`** desde un archivo **`.env`** en la raíz del repo (ver **`.env.example`**). El archivo **`.env`** no se versiona (`.gitignore`). |
| Base de datos | **PostgreSQL obligatorio** en local y producción (`psycopg` 3.x). Configuración: **`codas/settings/_database.py`**. **No se usa SQLite** — ver [`CODAS_DATABASE.md`](CODAS_DATABASE.md). |
| Punto de entrada | **`manage.py`** usa por defecto `DJANGO_SETTINGS_MODULE=codas.settings.local`. **`wsgi.py`** / **`asgi.py`** usan por defecto `codas.settings.production` (alinear con el despliegue si hace falta). |

*(Añade filas cuando fijéis nuevas decisiones, p. ej. API auxiliar, SSO.)*

### 6.1 Entornos y archivo `.env` (referencia rápida)

1. **Copiar plantilla:** duplicar `.env.example` como `.env` y completar valores en cada máquina o servidor.
2. **PostgreSQL (local y producción):** definir **`DATABASE_URL`** o **`DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT`** antes de `migrate` o `runserver`. Sin ello la app no arranca. Guía: [`CODAS_DATABASE.md`](CODAS_DATABASE.md).
3. **Desarrollo local:** con `manage.py`, por defecto se cargan **`codas.settings.local`**. Si no defines `DJANGO_SECRET_KEY`, se usa una clave solo para desarrollo (no usar en producción). `DJANGO_DEBUG` por defecto es **True** en local si no se indica lo contrario.
4. **Producción:** usar **`codas.settings.production`** (p. ej. variable de entorno del sistema o proceso WSGI/ASGI). Son **obligatorios** `DJANGO_SECRET_KEY`, **`DJANGO_ALLOWED_HOSTS`** (lista separada por comas) y **conexión PostgreSQL**. `DEBUG` queda en **False**.
5. **Logs:** en `base.py` hay un `LOGGING` básico hacia consola; el nivel se puede ajustar con **`DJANGO_LOG_LEVEL`** (por defecto `INFO`).

| Variable | Uso |
|----------|-----|
| `DJANGO_SECRET_KEY` | Clave secreta Django; obligatoria en producción. |
| `DJANGO_DEBUG` | `True`/`False` (o `1`/`0`); en `production` el código fuerza `DEBUG=False`. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por comas; obligatorio en producción. |
| `DJANGO_LOG_LEVEL` | Nivel de log (p. ej. `INFO`, `DEBUG`, `WARNING`). |
| `DATABASE_URL` | URL PostgreSQL (`postgresql://usuario:pass@host:puerto/nombre_bd`). Alternativa a variables `DB_*`. |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | Conexión PostgreSQL si no se usa `DATABASE_URL`. |
| `DB_CONN_MAX_AGE` | Opcional; segundos de reutilización de conexión (p. ej. `600` en producción). |
| `DB_SSLMODE` | Opcional; p. ej. `require` en PostgreSQL gestionado en la nube. |

### 6.2 Base de datos — PostgreSQL (resumen)

- **Motor único:** PostgreSQL en **local** (`codas.settings.local`) y **producción** (`codas.settings.production`).
- **Driver:** `psycopg[binary]>=3.1,<4` en `requirements.txt`.
- **Settings:** [`codas/settings/_database.py`](../codas/settings/_database.py) construye `DATABASES`; no existe fallback a SQLite.
- **Migraciones:** `python manage.py migrate` contra la instancia PostgreSQL configurada en `.env`.
- **Documentación ampliada:** [CODAS_DATABASE.md](CODAS_DATABASE.md) (instalación, variables, despliegue, backups). **Proveedores web:** [CODAS_DEPLOYMENT.md](CODAS_DEPLOYMENT.md). **PythonAnywhere (ZIP):** [CODAS_DEPLOYMENT_PYTHONANYWHERE.md](CODAS_DEPLOYMENT_PYTHONANYWHERE.md). **Railway (Git):** [CODAS_DEPLOYMENT_RAILWAY.md](CODAS_DEPLOYMENT_RAILWAY.md) — [checklist](CODAS_DEPLOYMENT_RAILWAY_CHECKLIST.md).

### 6.3 Reglas globales (plantillas Django)

Normas transversales que el motor de plantillas de Django aplica con rigor; incumplirlas provoca `TemplateSyntaxError` en tiempo de renderizado, a veces solo al navegar a una vista concreta.

- **Nombres de variables en plantillas:** **no** usar identificadores que comiencen por el carácter de subrayado **`_`**. Aplica a variables creadas con `{% with %}`, a atributos resueltos con el punto (`.`) y, en la práctica, a cualquier nombre de variable en el lenguaje de plantillas. El subrayado inicial está reservado para usos internos del compilador; por ejemplo, `{% with _tid=... %}` o `{{ obj._field }}` pueden fallar con *«Variables and attributes may not begin with underscores»*. Usar nombres explícitos (`sql_toolbar_textarea_id`, `download_label`, `item_class`, etc.) o prefijos legibles del dominio.

*(Complementa a `.cursorrules` y a las convenciones de templates del proyecto; no sustituye la guía de estilos HTML/Tailwind.)*

### 6.4 Mensajes de operación y modal (catálogo oficial)

Decisiones para **crear, leer, buscar, actualizar y eliminar** sin romper el flujo ni exponer errores técnicos al usuario.

| Tema | Decisión |
|------|----------|
| **Catálogo completo** | [`CODAS_UI_MESSAGES.md`](CODAS_UI_MESSAGES.md) — textos, `error_code` y tags `messages`. |
| **Presentación** | `django.contrib.messages` → modal `#codas-msg-modal` en `dashboard_base.html` (panel). |
| **Persistencia** | Servicios devuelven **`OperationResult`** (`ok`, `data`, `error_message`, `error_code`); implementación en `apps/core/services/` (fase 2+). |
| **Validación** | Formularios Django primero (`form.errors` en pantalla); ORM/BD después vía `safe_operation`. |
| **Error en POST de escritura** | **Re-render** de la misma vista; **no** redirect (el usuario no pierde lo escrito). |
| **Éxito** | `messages.success` + redirect al detalle o listado. |
| **Logs** | Detalle técnico solo en logs; nunca SQL ni `str(exception)` en el modal. |
| **Alcance implementación** | **`apps.company`** y **`apps.table_design`** (cabecera + campos CRUD). Resto de apps sin cambio hasta checklist § 0. |
| **Validación piloto** | Tests y checklist: [`CODAS_COMPANY_PILOT_CHECKLIST.md`](CODAS_COMPANY_PILOT_CHECKLIST.md) § 0–6 (`company`, `table_design`, `userprofile`, `sp_asistido` hechos). |

**Mensajes resumidos (ver tabla completa en el documento enlazado):**

- Éxito guardar: *«El registro se guardó correctamente.»*
- Formulario inválido: *«Revise los datos marcados en rojo; no se pudo guardar.»*
- Duplicado: *«Ya existe un registro con ese identificador…»*
- No encontrado: *«No se encontró el registro solicitado.»*
- Eliminar con relaciones: *«No se puede eliminar: existen datos asociados…»*
- Error inesperado: *«Ocurrió un error al guardar. Si persiste, contacte al administrador de sistemas.»*

---

## 7. Roadmap oficial

⭐ ROADMAP OFICIAL DEL PROYECTO CODAS (Versión desde CERO)
Arquitectura, módulos, UI, automatización y plataforma completa
⭐ FASE 0 — Preparación del Entorno y Base Técnica (Semana 1)
Objetivo: Crear la base sólida del proyecto.

✔ 0.1. Configuración del entorno
Python 3.12+
Virtualenv (`.venv`)
Django 6.x (`requirements.txt`)
PostgreSQL + **`psycopg[binary]`** (local y producción; ver **`docs/CODAS_DATABASE.md`**)
Settings por entorno: **`codas.settings.local`** y **`codas.settings.production`** (`codas/settings/`)
Variables con **`python-dotenv`** y archivo **`.env`** (plantilla **`.env.example`**, incl. `DATABASE_URL` o `DB_*`)
Logging en `LOGGING` (consola; nivel `DJANGO_LOG_LEVEL`)

✔ 0.2. Configuración de Tailwind CSS
Instalación de Tailwind
tailwind.config.js corporativo
package.json con scripts dev/build
tailwind.css base
Integración con Django

✔ 0.3. Configuración de Cursor AI
.cursorrules corporativo
cursor.json
Reglas de generación de código
Reglas de documentación
Reglas de UI

📌 Resultado:  
CODAS tiene una base técnica moderna, limpia y lista para crecer.

⭐ FASE 1 — Arquitectura del Proyecto (semana 2)
Objetivo: Definir la estructura modular definitiva.

✔ 1.1. Estructura de carpetas
Código (convención actual del repo: apps bajo `apps/`, settings en `codas/`)
apps/
    core/              # layout, landing, componentes base
    compania/
    seguridad/
    usuarios/
    tablas/
    sp_dinamico/
    sp_asistido/
    generador_scripts/
templates/             # opcional: fragmentos globales (p. ej. shared/)
static/

✔ 1.2. Componentes base
Navbar
Sidebar
Footer
Dashboard layout
Componentes reutilizables:
input
select
textarea
table
card
modal
alert
button

✔ 1.3. Base.html corporativo
Tema dark
Layout responsivo
Sidebar fijo
Navbar con usuario y notificaciones

📌 Resultado:  
CODAS tiene una arquitectura limpia, escalable y profesional.

⭐ FASE 2 — Página Inicial y Landing Page (Semana 3)
Objetivo: Crear la identidad visual del producto.

✔ 2.1. Landing Page corporativa
Hero premium
Sección “¿Qué es CODAS?”
Módulos
Beneficios
Contacto

✔ 2.2. Login corporativo
UI moderna
Validación
Branding CODAS

📌 Resultado:  
CODAS tiene una presencia visual profesional desde el día 1.

⭐ FASE 3 — Módulo Compañía (Semana 4)
Objetivo: Crear la base organizacional del sistema.
✔ 3.1. Modelo Compañía
Datos generales
Estado
Auditoría

✔ 3.2. CRUD completo
Listado
Crear
Editar
Eliminar

✔ 3.3. Integración con seguridad
Permisos por compañía
Roles por compañía

📌 Resultado:  
CODAS soporta múltiples compañías y estructuras.

⭐ FASE 4 — Módulo Seguridad (Semana 5)
Objetivo: Crear la base de seguridad corporativa.

✔ 4.1. Usuarios
Modelo usuario extendido
Roles
Permisos
Auditoría

✔ 4.2. Autenticación
Login
Logout
Recuperación de contraseña
MFA opcional

✔ 4.3. Autorización
Decoradores
Middleware

Control por módulo y acción

📌 Resultado:  
CODAS es seguro, auditable y apto para entornos empresariales.

⭐ FASE 5 — Módulo Tablas BD2 (Semana 6)
Objetivo: Crear el diseñador de tablas para IBM i.

✔ 5.1. Modelo de tabla
Nombre
Descripción
Auditoría

✔ 5.2. Modelo de columnas
Tipo de dato BD2
Longitud
Decimales
PK
FK
Nulos

✔ 5.3. Wizard de creación de tablas
Paso 1: Datos generales
Paso 2: Columnas
Paso 3: Validación
Paso 4: Generación de script

✔ 5.4. Generación de script BD2
CREATE TABLE
Constraints
Comentarios

📌 Resultado:  
CODAS genera tablas BD2 listas para producción.

⭐ FASE 6 — Módulo SP Dinámico (Semana 7)
Objetivo: Crear un generador de SP basado en metadatos.
✔ 6.1. Selección de tabla
✔ 6.2. Selección de columnas
✔ 6.3. Definición de filtros
✔ 6.4. Definición de orden
✔ 6.5. Generación automática del SP
✔ 6.6. Documentación automática
📌 Resultado:  
CODAS genera SP SELECT dinámicos sin intervención manual.

⭐ FASE 7 — Módulo SP Asistido (Semana 8)
Objetivo: Crear wizards inteligentes para SP complejos.
✔ 7.1. Wizard SELECT
✔ 7.2. Wizard INSERT
✔ 7.3. Wizard UPDATE
✔ 7.4. Wizard DELETE
✔ 7.5. Validación por paso
✔ 7.6. Generación del script final
✔ 7.7. App Django `apps.sp_asistido` (modelos, wizards completos READ/ADD/UPD/DLT, listado, acceso por compañía, generación de script **§9** en `services/`, pruebas automatizadas) — documentación canónica en [`docs/CODAS_SP_ASISTIDO.md`](CODAS_SP_ASISTIDO.md) (el documento de checklist operativo de desarrollo se archivó en abr. 2026; no se mantiene en repo).
📌 Resultado:  
CODAS permite crear SP empresariales con control total; el módulo SP Asistido está operativo en panel con trazabilidad, seguridad básica (IDOR, POST) y criterios de aceptación del script documentados.

⭐ FASE 8 — Generador de Scripts (Semana 9)
Objetivo: Crear un módulo avanzado de automatización.
✔ 8.1. Plantillas corporativas
✔ 8.2. Variables dinámicas
✔ 8.3. Versionado automático
✔ 8.4. Comparación de scripts
✔ 8.5. Exportación
📌 Resultado:  
CODAS se convierte en una herramienta de automatización real.

⭐ FASE 9 — Documentación, QA y Lanzamiento (Semana 10)
✔ Manual de usuario
✔ Manual técnico
✔ Documentación de arquitectura
✔ Pruebas unitarias
✔ Pruebas de integración
✔ Pruebas de rendimiento
✔ Preparación para producción
📌 Resultado:  
CODAS queda listo para uso corporativo.

### Resumen del roadmap (desde cero)

| Fase | Objetivo | Semana orientativa |
|------|----------|-------------------|
| 0 | Base técnica (Python, Django, Tailwind, Cursor) | 1 |
| 1 | Arquitectura del proyecto | 2 |
| 2 | Landing + Login | 3 |
| 3 | Compañía | 4 |
| 4 | Seguridad + usuarios | 5 |
| 5 | Tablas BD2 | 6 |
| 6 | SP dinámico | 7 |
| 7 | SP asistido | 8 |
| 8 | Generador de scripts | 9 |
| 9 | QA + documentación + release | 10 |


---

## 8. Glosario breve

| Término | Significado en CODAS |
|---------|----------------------|
| SP | Store procedure |
| BD2 / IBM i | Base de datos y sistema en el contexto IBM i |
| Wizard | Flujo multipaso con plantilla por paso y estado en sesión |
| Artefacto | Script, definición o módulo generado para despliegue en IBM i |

---

## 9. Cómo usar este archivo con el asistente

- Para **alcance, prioridades o wording de producto**, indica que respete **`docs/CODAS_CONTEXTO.md`** o usa **@CODAS_CONTEXTO.md**.
- Para **entornos, `.env` o settings (local vs producción)**, revisa la **sección 6.1** de este mismo archivo.
- Para **convenciones de plantillas Django** (nombres de variables, `{% with %}`, evitar `_*`), revisa la **sección 6.2**.
- Para **flujos de seguridad y acceso (usuario nuevo, correo, 2FA)**, revisa **`docs/CODAS_SECURITY.md`** junto con **`docs/CODAS_MODELS.md`**.
- Tras acordar cambios importantes, **actualiza este documento** para mantener una sola fuente de verdad.

---

*Documento alineado al resumen ejecutivo, al roadmap (sección 7) y a las decisiones técnicas, entornos (6.1) y reglas de plantillas (6.2). Fase 7 (SP asistido) se considera **entregada en producto** respecto a wizards y listado; evolución futura en [`CODAS_SP_ASISTIDO.md`](CODAS_SP_ASISTIDO.md) y Fase 8. Actualizar cuando cambien fases, plazos o configuración de despliegue.*
