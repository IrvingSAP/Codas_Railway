# Checklist CODAS en Railway

Control operativo paso a paso para desplegar CODAS en [Railway](https://railway.app), alineado con la [documentación oficial de Railway](https://docs.railway.com/) y el estado actual del repositorio.

**Guía ampliada:** [CODAS_DEPLOYMENT_RAILWAY.md](CODAS_DEPLOYMENT_RAILWAY.md)  
**Relacionado:** [CODAS_DEPLOYMENT.md](CODAS_DEPLOYMENT.md), [CODAS_DATABASE.md](CODAS_DATABASE.md) § 6, [`.env.example`](../.env.example)

**Referencias Railway usadas:**

| Tema | Documento Railway |
|------|-------------------|
| Django + Gunicorn + WhiteNoise | [guides/django](https://docs.railway.com/guides/django) |
| PostgreSQL | [guides/postgresql](https://docs.railway.com/guides/postgresql) |
| Variables y referencias `${{...}}` | [guides/variables](https://docs.railway.com/guides/variables) |
| `railway.toml` (build, start, pre-deploy) | [reference/config-as-code](https://docs.railway.com/reference/config-as-code) |
| Dominio público HTTPS | [guides/public-networking](https://docs.railway.com/guides/public-networking) |
| Volúmenes (`media/`) | [guides/volumes](https://docs.railway.com/guides/volumes) |

---

## Registro de despliegue

| Campo | Valor |
|-------|--------|
| Cuenta Railway | |
| Proyecto | |
| Servicio Web | |
| Servicio PostgreSQL | |
| URL pública | `https://____________.up.railway.app` |
| Repositorio / rama | |
| Commit desplegado | |
| Fecha primer deploy | |
| Volumen `media/` (sí/no) | |

---

## Parte A — Actualizar el sistema CODAS (repositorio)

Completar **antes** del primer deploy. **A.1–A.5** completados en repo; pendiente push (A.7.3) y pasos Railway (B–H).

### A.1 Dependencias Python

| # | Tarea | Archivo | OK |
|---|--------|---------|-----|
| A.1.1 | Añadir `gunicorn>=22.0,<24` | [`requirements.txt`](../requirements.txt) | [x] |
| A.1.2 | Añadir `whitenoise>=6.6,<7` | [`requirements.txt`](../requirements.txt) | [x] |
| A.1.3 | Confirmar `psycopg[binary]` (ya está) | [`requirements.txt`](../requirements.txt) | [x] |

### A.2 Estáticos (WhiteNoise)

Según [guía Django de Railway](https://docs.railway.com/guides/django): `STATIC_ROOT` + middleware WhiteNoise tras `SecurityMiddleware`.

| # | Tarea | Archivo | OK |
|---|--------|---------|-----|
| A.2.1 | Definir `STATIC_ROOT = BASE_DIR / "staticfiles"` | [`codas/settings/production.py`](../codas/settings/production.py) | [x] |
| A.2.2 | Insertar `whitenoise.middleware.WhiteNoiseMiddleware` justo después de `SecurityMiddleware` | [`codas/settings/production.py`](../codas/settings/production.py) | [x] |
| A.2.3 | Añadir `staticfiles/` a `.gitignore` (generado en build) | [`.gitignore`](../.gitignore) | [x] |

### A.3 HTTPS y CSRF (dominio Railway)

| # | Tarea | Archivo | OK |
|---|--------|---------|-----|
| A.3.1 | `CSRF_TRUSTED_ORIGINS` desde env (lista separada por comas, con `https://`) | [`codas/settings/production.py`](../codas/settings/production.py) | [x] |
| A.3.2 | `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` | [`codas/settings/production.py`](../codas/settings/production.py) | [x] |
| A.3.3 | `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True` | [`codas/settings/production.py`](../codas/settings/production.py) | [x] |

### A.4 Tailwind (CSS)

Estrategia **A (Git)**: CSS compilado en local y versionado; el build de Railway **no** usa npm (Railpack Python no trae Node por defecto).

| # | Tarea | Comando / archivo | OK |
|---|--------|-------------------|-----|
| A.4.1 | Compilar CSS antes del deploy | `npm run build:css:min` | [x] |
| A.4.2 | **Opción A:** versionar [`static/css/tailwind.css`](../static/css/tailwind.css) en Git | commit | [x] |
| A.4.3 | **Opción B:** compilar en build Railway (requiere Node; no usado) | — | N/A |

### A.5 Configuración Railway en el repo

[`railway.toml`](../railway.toml) en la raíz ([config as code](https://docs.railway.com/reference/config-as-code)):

| # | Tarea | OK |
|---|--------|-----|
| A.5.1 | `buildCommand`: pip + `collectstatic --noinput` (sin npm) | [x] |
| A.5.2 | `migrate` en **startCommand** (no preDeploy; ver § J.3) | [x] |
| A.5.3 | `startCommand`: `gunicorn codas.wsgi:application --bind 0.0.0.0:$PORT` | [x] |

Plantilla orientativa:

```toml
[build]
buildCommand = "pip install -r requirements.txt && DJANGO_SETTINGS_MODULE=codas.settings.collectstatic_build python manage.py collectstatic --noinput"

[deploy]
startCommand = "DJANGO_SETTINGS_MODULE=codas.settings.production python manage.py migrate --noinput && gunicorn codas.wsgi:application --bind 0.0.0.0:$PORT"
restartPolicyType = "ON_FAILURE"
```

> Railway ejecuta `preDeployCommand` **antes** del arranque; no tiene acceso a volúmenes en esa fase ([volumes](https://docs.railway.com/guides/volumes)). Las migraciones van ahí; `createsuperuser` es manual (CLI).

### A.6 Lo que **no** cambiar / no commitear

| # | Regla | OK |
|---|--------|-----|
| A.6.1 | **No** commitear `.env` con secretos | [ ] |
| A.6.2 | **No** definir `EMAIL_BACKEND` en producción (lo asigna [`codas/settings/_email.py`](../codas/settings/_email.py)) | [ ] |
| A.6.3 | Mantener `DJANGO_SETTINGS_MODULE=codas.settings.production` en Railway, no en código | [ ] |
| A.6.4 | PostgreSQL obligatorio; **no** usar SQLite | [ ] |

### A.7 Verificación local antes de push

| # | Tarea | Comando | OK |
|---|--------|---------|-----|
| A.7.1 | Tests de email/settings | `python manage.py test apps.core.tests.test_email_settings apps.core.tests.test_production_settings` | [x] |
| A.7.2 | `collectstatic` local de prueba | variables producción + `python manage.py collectstatic --noinput --settings=codas.settings.production` | [x] |
| A.7.3 | Commit + push a la rama que desplegará Railway | `git push` | [ ] |

---

## Parte B — Cuenta y proyecto Railway

| # | Paso (panel [railway.app](https://railway.app)) | Doc Railway | OK |
|---|------------------------------------------------|-------------|-----|
| B.1 | Crear cuenta / iniciar sesión | [Quick start](https://docs.railway.com/) | [ ] |
| B.2 | **New Project** | | [ ] |
| B.3 | **Deploy from GitHub repo** → autorizar GitHub → elegir repo CODAS | [guides/django](https://docs.railway.com/guides/django) | [ ] |
| B.4 | Seleccionar rama de deploy (`main`) | | [ ] |
| B.5 | Renombrar servicio a `codas-web` (opcional, claridad) | | [ ] |

---

## Parte C — PostgreSQL en Railway

| # | Paso | Doc Railway | OK |
|---|------|-------------|-----|
| C.1 | En el canvas: **Create** → **Database** → **Add PostgreSQL** | [guides/postgresql](https://docs.railway.com/guides/postgresql) | [ ] |
| C.2 | Esperar deploy del servicio Postgres (estado activo) | | [ ] |
| C.3 | En servicio **Web** → **Variables** → referenciar `DATABASE_URL` | [guides/variables](https://docs.railway.com/guides/variables) | [ ] |

Valor de referencia (ajustar nombre del servicio Postgres):

```ini
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

> CODAS usa `DATABASE_URL` vía [`codas/settings/_database.py`](../codas/settings/_database.py). Railway también expone `PGHOST`, `PGUSER`, etc.; no son necesarios si usas `DATABASE_URL`.

| # | Paso | OK |
|---|------|-----|
| C.4 | (Opcional) Activar backups del Postgres en producción | [ ] |

---

## Parte D — Variables de entorno (servicio Web)

En **Variables** del servicio Web. Usar **Raw Editor** o **New Variable**. Los cambios quedan en staging hasta **Deploy** ([variables](https://docs.railway.com/guides/variables)).

### D.1 Django y secretos

| Variable | Valor | Sellada | OK |
|----------|--------|---------|-----|
| `DJANGO_SETTINGS_MODULE` | `codas.settings.production` | No | [ ] |
| `DJANGO_SECRET_KEY` | Clave aleatoria larga | **Sí** | [ ] |
| `LICENSE_SECRET_KEY` | Clave HMAC suscripciones | **Sí** | [ ] |
| `DJANGO_ALLOWED_HOSTS` | Dominio **literal** (recomendado) o `${{RAILWAY_PUBLIC_DOMAIN}}` | No | [ ] |
| `CSRF_TRUSTED_ORIGINS` | `https://tu-dominio.up.railway.app` o `https://${{RAILWAY_PUBLIC_DOMAIN}}` | No | [ ] |

### D.2 Base de datos

| Variable | Valor | OK |
|----------|--------|-----|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | [ ] |

### D.3 Correo SMTP (obligatorio en producción)

| Variable | Valor ejemplo | Sellada | OK |
|----------|---------------|---------|-----|
| `EMAIL_DELIVERY` | `smtp` | No | [ ] |
| `EMAIL_HOST` | `smtp.gmail.com` | No | [ ] |
| `EMAIL_PORT` | `587` | No | [ ] |
| `EMAIL_USE_TLS` | `True` | No | [ ] |
| `EMAIL_HOST_USER` | cuenta Gmail | No | [ ] |
| `EMAIL_HOST_PASSWORD` | contraseña de aplicación (sin espacios) | **Sí** | [ ] |
| `DEFAULT_FROM_EMAIL` | mismo que `EMAIL_HOST_USER` | No | [ ] |

**No** definir `EMAIL_BACKEND` — lo asigna `_email.py`.

**Plantilla Raw Editor (proyecto Codas_Railway — ajustar nombres):**

```ini
DJANGO_SETTINGS_MODULE=codas.settings.production
DJANGO_SECRET_KEY=...
LICENSE_SECRET_KEY=...
DJANGO_ALLOWED_HOSTS=tu-servicio.up.railway.app
CSRF_TRUSTED_ORIGINS=https://tu-servicio.up.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
EMAIL_DELIVERY=smtp
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=sin-espacios
DEFAULT_FROM_EMAIL=...
```

> `DATABASE_URL`: usar **Add Reference** al servicio PostgreSQL (nombre típico `Postgres`).  
> `EMAIL_HOST_PASSWORD`: contraseña de aplicación Gmail **sin espacios**.  
> Tras **Generate Domain**, copiar el hostname a `DJANGO_ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` (más fiable que solo referencias en el primer deploy).

### D.4 Aplicar variables

| # | Paso | OK |
|---|------|-----|
| D.4.1 | Revisar diff de variables staged | [ ] |
| D.4.2 | **Deploy** del servicio Web para aplicar variables | [ ] |

---

## Parte E — Build, dominio y networking

| # | Paso | Doc Railway | OK |
|---|------|-------------|-----|
| E.1 | Confirmar `railway.toml` en repo (o comandos en Settings → Deploy) | [config-as-code](https://docs.railway.com/reference/config-as-code) | [ ] |
| E.2 | **Settings** → comprobar **Root Directory** (vacío si `manage.py` está en raíz) | | [ ] |
| E.3 | **Settings** → **Networking** → **Generate Domain** | [public-networking](https://docs.railway.com/guides/public-networking) | [ ] |
| E.4 | Copiar URL `https://….up.railway.app` al registro de despliegue | | [ ] |
| E.5 | Si `DJANGO_ALLOWED_HOSTS` era fijo, actualizarlo con el dominio generado | | [ ] |
| E.6 | **Deploy** (o push a Git si CI conectado) | | [ ] |

### E.1 Revisar logs de build

| # | Comprobar en Deploy Logs | OK |
|---|------------------------|-----|
| E.1.1 | `pip install -r requirements.txt` sin error | [ ] |
| E.1.2 | `npm run build:css:min` (si aplica) | [ ] |
| E.1.3 | `collectstatic` copió archivos a `staticfiles/` | [ ] |
| E.1.4 | `startCommand`: `migrate` + Gunicorn (no preDeploy) | [ ] |
| E.1.5 | Gunicorn enlazado a `$PORT` | [ ] |

---

## Parte F — Media / logos (opcional)

Por defecto el disco del contenedor es **efímero**; `media/` se pierde al redeploy.

| # | Estrategia | Paso | OK |
|---|------------|------|-----|
| F.1 | **Demo sin logos** | No hacer nada | [ ] |
| F.2 | **Persistir logos** | Servicio Web → **Volumes** → montar en `/app/media` | [guides/volumes](https://docs.railway.com/guides/volumes) | [ ] |
| F.3 | Si imagen no-root | `RAILWAY_RUN_UID=0` (Railway lo indica para permisos de volumen) | [ ] |

`MEDIA_ROOT` en CODAS = `BASE_DIR / "media"` → en contenedor suele ser `/app/media`.

---

## Parte G — Datos iniciales (una vez)

| # | Paso | Comando / acción | OK |
|---|------|------------------|-----|
| G.1 | Crear superusuario | `railway link` + `railway run python manage.py createsuperuser` | [ ] |
| G.2 | (Opcional) Cargar compañías / datos piloto | según checklist piloto | [ ] |

---

## Parte H — Smoke test post-deploy

| # | Prueba | URL / acción | OK |
|---|--------|--------------|-----|
| H.1 | App en verde | Deploy Logs sin traceback | [ ] |
| H.2 | Login | `/ingresar/` | [ ] |
| H.3 | Panel | `/panel/` | [ ] |
| H.4 | Tailwind cargado | CSS visible, no HTML crudo | [ ] |
| H.5 | Admin | `/admin/` | [ ] |
| H.6 | POST sin CSRF 403 | Crear/editar registro en un flujo | [ ] |
| H.7 | Correo (si aplica) | Confirmación / reset password | [ ] |
| H.8 | Flujo dominio | table-design o sp-asistido | [ ] |

### Errores frecuentes

| Síntoma | Revisar |
|---------|---------|
| `DisallowedHost` | `DJANGO_ALLOWED_HOSTS` = dominio Railway exacto |
| CSRF 403 | `CSRF_TRUSTED_ORIGINS=https://…` en settings + variable |
| `ImproperlyConfigured` al arrancar | SMTP incompleto o `EMAIL_BACKEND` en env |
| Estáticos 404 | WhiteNoise + `collectstatic` en build |
| BD no conecta | `DATABASE_URL=${{Postgres.DATABASE_URL}}` + Deploy aplicado |
| Build falla en `collectstatic` / PostgreSQL no configurada | Usar `codas.settings.collectstatic_build` en build (ver [`collectstatic_build.py`](../codas/settings/collectstatic_build.py)) |
| `DATABASE_URL` / no database configured | Servicio **PostgreSQL** + referencia `${{Postgres.DATABASE_URL}}` en el servicio Web (**Add Reference**) |
| `DJANGO_ALLOWED_HOSTS es obligatorio` en **pre-deploy** | `${{RAILWAY_PUBLIC_DOMAIN}}` **no se expande** en pre-deploy; ver § J.3 — usar dominio literal o `migrate` en start |
| IA Railway sugiere `DJANGO_ALLOWED_HOSTS=*` | Evitar en producción; usar dominio literal tras **Generate Domain** |
| Variables guardadas pero sigue fallando | Hacer **Deploy** tras staged variables (el deploy anterior no las tenía) |

---

## Parte J — Lecciones del despliegue real (Codas_Railway)

Incidencias resueltas en el primer deploy con IA de Railway y ajustes en el repo.

### J.1 PostgreSQL → servicio Web

| Paso | Detalle |
|------|---------|
| 1 | Canvas → **Add PostgreSQL** (servicio aparte del Web) |
| 2 | Servicio **Codas_Railway** (Web) → **Variables** → **Add Reference** |
| 3 | Elegir Postgres → `DATABASE_URL` → queda `${{Postgres.DATABASE_URL}}` |
| 4 | **Deploy** para aplicar variables staged |

Sin referencia, el pre-deploy/start falla con *no database is configured*.

### J.2 Variables obligatorias de producción

CODAS valida al importar `codas.settings.production`:

| Variable | Cómo obtenerla |
|----------|----------------|
| `DJANGO_SECRET_KEY` | Clave aleatoria larga (sellada) |
| `LICENSE_SECRET_KEY` | Otra clave aleatoria (sellada) |
| `DJANGO_ALLOWED_HOSTS` | Hostname del dominio Railway **sin** `https://` |
| `CSRF_TRUSTED_ORIGINS` | `https://` + mismo hostname |
| `DATABASE_URL` | Referencia al Postgres |
| `EMAIL_*` | SMTP Gmail (password **sin espacios**) |

### J.3 `${{RAILWAY_PUBLIC_DOMAIN}}` y pre-deploy

**Problema observado:** con `preDeployCommand` + `migrate` usando `production`, Django exige `DJANGO_ALLOWED_HOSTS`. Si la variable es `${{RAILWAY_PUBLIC_DOMAIN}}`, en la fase **pre-deploy** puede llegar **vacía** (el dominio aún no está disponible en ese momento).

**Solución en el repo (desde jun/2026):** [`railway.toml`](../railway.toml) ejecuta `migrate` en **startCommand**, junto a Gunicorn, cuando las variables de runtime ya están expandidas.

**Alternativa manual:** tras **Generate Domain**, usar valores **literales**:

```ini
DJANGO_ALLOWED_HOSTS=codas-railway-production.up.railway.app
CSRF_TRUSTED_ORIGINS=https://codas-railway-production.up.railway.app
```

**No recomendado:** `DJANGO_ALLOWED_HOSTS=*` (atajo de la IA Railway; inseguro en producción).

### J.4 Orden recomendado en Railway

```mermaid
flowchart LR
  PG[Add_PostgreSQL] --> REF[Add_Reference_DATABASE_URL]
  REF --> DOM[Generate_Domain]
  DOM --> VARS[Variables_secretos_SMTP_hosts]
  VARS --> DEPLOY[Deploy]
  DEPLOY --> SU[createsuperuser]
```

1. PostgreSQL activo  
2. Referencia `DATABASE_URL` en Web  
3. **Generate Domain**  
4. Variables completas (hosts literales o `${{RAILWAY_PUBLIC_DOMAIN}}` con migrate en start)  
5. **Deploy** (no confiar en un deploy anterior sin variables)  
6. Pull del último `railway.toml` (migrate en start)  
7. `createsuperuser` + smoke test  

### J.5 Asistente IA de Railway

Útil para: enlazar Postgres, generar `LICENSE_SECRET_KEY`, revisar diagnóstico.  
Verificar siempre: no dejar `ALLOWED_HOSTS=*`, password Gmail sin espacios, y **Deploy** tras cambios staged.

### J.6 Otros errores ya corregidos en el repo

| Error | Solución |
|-------|----------|
| `npm: not found` en build | Sin npm en build; Tailwind versionado en Git |
| `collectstatic` + `local.py` / sin BD | `DJANGO_SETTINGS_MODULE=codas.settings.collectstatic_build` en build |

---

## Parte I — Actualizaciones posteriores

| # | Paso | OK |
|---|------|-----|
| I.1 | Desarrollo local + tests | [ ] |
| I.2 | `npm run build:css:min` si hubo cambios CSS | [ ] |
| I.3 | `git commit` + `git push` a rama conectada | [ ] |
| I.4 | Railway redeploy automático | [ ] |
| I.5 | Verificar logs: `migrate` en **start** + Gunicorn | [ ] |
| I.6 | Smoke test rápido en producción | [ ] |

---

## Resumen ejecutivo (orden recomendado)

```mermaid
flowchart TD
  A[Parte_A_Repo_CODAS] --> B[Parte_B_Proyecto_Railway]
  B --> C[Parte_C_PostgreSQL]
  C --> D[Parte_D_Variables]
  D --> E[Parte_E_Build_y_dominio]
  E --> F[Parte_F_Media_opcional]
  E --> G[Parte_G_Superusuario]
  G --> H[Parte_H_Smoke_test]
```

| Fase | Bloque | Ítems críticos |
|------|--------|----------------|
| 1 | **A** — Repo | gunicorn, whitenoise, STATIC_ROOT, railway.toml, CSS |
| 2 | **B–C** — Railway | GitHub, Postgres, `DATABASE_URL` referenciada |
| 3 | **D** — Variables | Secretos, SMTP, hosts, CSRF |
| 4 | **E** — Deploy | Dominio público, logs verdes |
| 5 | **G–H** — Go-live | superuser, smoke test |

---

## Checklist global (una página)

| # | Tarea | OK |
|---|--------|-----|
| 1 | Repo en GitHub + `railway.toml` actualizado (migrate en start) | [ ] |
| 2 | Repo: CSS compilado en Git | [ ] |
| 3 | Railway: proyecto + repo conectado | [ ] |
| 4 | Railway: PostgreSQL + `DATABASE_URL` referenciada | [ ] |
| 5 | Railway: variables Django, secretos, SMTP (sin EMAIL_BACKEND) | [ ] |
| 6 | Railway: dominio público generado | [ ] |
| 7 | Deploy verde: build + migrate + gunicorn | [ ] |
| 8 | `createsuperuser` + smoke test | [ ] |
| 9 | (Opcional) volumen `/app/media` | [ ] |

---

*Última revisión: jun/2026 — lecciones deploy Codas_Railway (Postgres, pre-deploy, migrate en start).*
