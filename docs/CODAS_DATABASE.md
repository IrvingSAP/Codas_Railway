# CODAS — Base de datos (PostgreSQL)

Documento de referencia para el **motor de datos** del proyecto. Fuente de verdad del código: [`codas/settings/_database.py`](../codas/settings/_database.py), [`codas/settings/local.py`](../codas/settings/local.py), [`codas/settings/production.py`](../codas/settings/production.py).

**Decisión de producto (jun/2026):** CODAS usa **PostgreSQL** en **desarrollo local** y en **producción**. **No** se utiliza SQLite ni el archivo `db.sqlite3` como persistencia de la aplicación.

---

## 1. Stack

| Componente | Detalle |
|------------|---------|
| Motor | **PostgreSQL** 14+ (recomendado 16 en local) |
| Driver Python | **`psycopg[binary]`** 3.x (`requirements.txt`) |
| ORM | Django 6.x — migraciones en `apps/*/migrations/` |
| Configuración | Variables en **`.env`** (plantilla [`.env.example`](../.env.example)) |

---

## 2. Entornos Django

| Entorno | Módulo settings | Base de datos |
|---------|-----------------|---------------|
| Desarrollo | `codas.settings.local` (`manage.py` por defecto) | PostgreSQL (obligatorio) |
| Producción | `codas.settings.production` (`wsgi.py` / `asgi.py`) | PostgreSQL (obligatorio) |

Ambos llaman a `build_databases_settings()` y validan la configuración al importar el módulo (`validate_database_settings()`).

**No hay** rama SQLite en settings: si faltan credenciales, Django falla al arrancar con `ImproperlyConfigured` y un mensaje que remite a `.env.example`.

---

## 3. Variables de entorno

### Opción A — URL (recomendada)

```env
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/codas_dev
```

### Opción B — variables sueltas

```env
DB_NAME=codas_dev
DB_USER=codas
DB_PASSWORD=contraseña
DB_HOST=localhost
DB_PORT=5432
```

### Opcionales

| Variable | Uso |
|----------|-----|
| `DB_CONN_MAX_AGE` | Reutilización de conexión en segundos (p. ej. `600` en producción). |
| `DB_SSLMODE` | p. ej. `require` en PostgreSQL gestionado (PythonAnywhere addon, Neon, Supabase). |
| `DB_TEST_NAME` | Nombre de la BD de pruebas si se creó a mano (§ 5); p. ej. `test_codas_dev`. |

---

## 4. Puesta en marcha local

1. Instalar y arrancar PostgreSQL (servicio en Windows, Docker, etc.).
2. Crear base y usuario (ejemplo):

```sql
CREATE USER codas WITH PASSWORD 'tu_contraseña';
CREATE DATABASE codas_dev OWNER codas;
```

3. Copiar `.env.example` → `.env` y definir `DATABASE_URL` o `DB_*`.
4. Activar venv e instalar dependencias: `pip install -r requirements.txt`.
5. Aplicar esquema: `python manage.py migrate`.
6. Datos iniciales opcionales: admin (`createsuperuser`), compañías, etc.

---

## 5. Tests (`manage.py test`)

Django crea por defecto una base `test_<DB_NAME>` (p. ej. `test_codas_dev`). Si el usuario de `.env` **no** tiene permiso `CREATEDB`, verá:

`Got an error creating the test database: se ha denegado el permiso para crear la base de datos`

### Opción A — Dar permiso al usuario de la app (recomendado en local)

Conecte como superusuario (`postgres`) en `psql` o pgAdmin:

```sql
ALTER USER codas CREATEDB;
```

Sustituya `codas` por el valor de `DB_USER` o el usuario de su `DATABASE_URL`. Luego:

```powershell
python manage.py test apps.company.tests
```

### Opción B — Crear la BD de prueba a mano (sin CREATEDB)

1. Como superusuario, cree la base y asígnela al mismo rol que usa CODAS:

```sql
CREATE DATABASE test_codas_dev OWNER codas;
GRANT ALL PRIVILEGES ON DATABASE test_codas_dev TO codas;
```

2. En `.env`, opcional pero explícito:

```env
DB_TEST_NAME=test_codas_dev
```

3. Ejecute los tests **reutilizando** esa base (no intenta `CREATE DATABASE` si ya existe):

```powershell
python manage.py test apps.company.tests --keepdb
```

La primera vez con `--keepdb`, Django aplica migraciones sobre `test_codas_dev`. En ejecuciones siguientes será más rápido.

### Comando en PowerShell

Use siempre el intérprete Python, no `manage.py` a secas:

```powershell
python manage.py test apps.company.tests --keepdb
```

---

## 6. Producción y despliegue

- **Guía de proveedores y alternativas web:** [CODAS_DEPLOYMENT.md](CODAS_DEPLOYMENT.md).
- **PythonAnywhere por ZIP (control de despliegue):** [CODAS_DEPLOYMENT_PYTHONANYWHERE.md](CODAS_DEPLOYMENT_PYTHONANYWHERE.md).
- **Railway por Git (control de despliegue):** [CODAS_DEPLOYMENT_RAILWAY.md](CODAS_DEPLOYMENT_RAILWAY.md) — checklist: [CODAS_DEPLOYMENT_RAILWAY_CHECKLIST.md](CODAS_DEPLOYMENT_RAILWAY_CHECKLIST.md).
- **PythonAnywhere:** addon PostgreSQL o instancia externa; mismas variables en el `.env` del Web app; `DJANGO_SETTINGS_MODULE=codas.settings.production`.
- **Backup:** `pg_dump` / herramientas del proveedor — **no** copiar `db.sqlite3` (obsoleto para CODAS).
- **Migraciones:** desplegar código y ejecutar `python manage.py migrate` contra la BD de producción (ventana de mantenimiento si aplica).

---

## 7. Migraciones Django

- Generar: `python manage.py makemigrations`
- Aplicar: `python manage.py migrate`
- Tras regenerar migraciones desde cero (solo en desarrollo controlado), usar una BD PostgreSQL **vacía** o un esquema nuevo antes de `migrate`.

El historial actual del repo parte de migraciones `0001_initial` por app (regeneración may/2026).

---

## 8. Lo que ya no aplica

| Antes (obsoleto) | Ahora |
|------------------|--------|
| `db.sqlite3` en la raíz del repo | No usar; puede quedar en `.gitignore` por restos locales |
| `django.db.backends.sqlite3` en settings | Eliminado |
| Desarrollo en SQLite / producción sin BD configurada | Ambos entornos exigen PostgreSQL |

---

## 9. Referencias cruzadas

- Decisiones generales y tabla resumida de variables: [CODAS_CONTEXTO.md](CODAS_CONTEXTO.md) § 6 y § 6.1.
- Modelos de dominio: [CODAS_MODELS.md](CODAS_MODELS.md).
- Despliegue web y proveedores: [CODAS_DEPLOYMENT.md](CODAS_DEPLOYMENT.md).
- PythonAnywhere (ZIP): [CODAS_DEPLOYMENT_PYTHONANYWHERE.md](CODAS_DEPLOYMENT_PYTHONANYWHERE.md).
- Railway (Git): [CODAS_DEPLOYMENT_RAILWAY.md](CODAS_DEPLOYMENT_RAILWAY.md) — [checklist](CODAS_DEPLOYMENT_RAILWAY_CHECKLIST.md).

*Última revisión: jun/2026 — PostgreSQL obligatorio en local y producción; driver `psycopg` 3.x.*
