# CODAS — Procedimiento: llave de integridad (`LICENSE_SECRET_KEY`) y alta de suscripción

**Propósito:** describir, alineado con el código actual, cómo se configura el secreto del sistema para las huellas HMAC de `Subscription`, cómo se da de alta una suscripción y qué validaciones existen en tiempo de ejecución.

**Referencias:**

- Modelos y relaciones: [`CODAS_MODELS.md`](CODAS_MODELS.md) (sección `apps.billing`).
- Diseño y amenazas: [`CODAS_SUSCRIPCIONES_VALIDACION.md`](CODAS_SUSCRIPCIONES_VALIDACION.md).
- Código: [`apps/billing/models.py`](../apps/billing/models.py), [`apps/billing/services/license.py`](../apps/billing/services/license.py), [`codas/settings/base.py`](../codas/settings/base.py).

---

## 1. Generación de la llave maestra del sistema (`LICENSE_SECRET_KEY`)

La “llave maestra” **no es por compañía**: es **un único secreto** en el entorno del servidor que usa la aplicación para calcular `integrity_signature` en cada `Subscription` (HMAC-SHA256 sobre las fechas de vigencia en formato canónico).

### 1.1 Generar un valor aleatorio seguro

En **Linux/macOS** (Bash):

```bash
python - << 'EOF'
import secrets
print(secrets.token_hex(32))
EOF
```

En **Windows (PowerShell o CMD)**, equivalente:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

`token_hex(32)` produce 64 caracteres hexadecimales (32 bytes de entropía), adecuado como secreto compartido.

Copiar el valor generado y **no** commitearlo al repositorio.

### 1.2 Configurar el entorno del servidor

En el archivo **`.env`** del despliegue (el proyecto carga `BASE_DIR/.env` en [`codas/settings/base.py`](../codas/settings/base.py)):

```env
LICENSE_SECRET_KEY=<valor_generado>
```

Reiniciar el proceso del servidor (Gunicorn, uwsgi, servicio Windows, contenedor, etc.) para que la variable esté disponible.

### 1.3 Producción

`validate_production()` exige que exista `LICENSE_SECRET_KEY` en el entorno cuando se valida la configuración de producción (ver [`codas/settings/base.py`](../codas/settings/base.py)).

---

## 2. Configuración en el proyecto CODAS

**No es necesario añadir a mano** una nueva línea en `settings.py` si ya usas la base del repositorio: la variable ya se enlaza al entorno:

```python
LICENSE_SECRET_KEY = os.environ.get("LICENSE_SECRET_KEY", "")
```

([`codas/settings/base.py`](../codas/settings/base.py).)

### 2.1 Desarrollo local (`DEBUG=True`)

Si `LICENSE_SECRET_KEY` está vacío pero `DEBUG` es verdadero, el modelo puede usar `SECRET_KEY` de Django como respaldo para calcular la firma (ver [`apps/billing/models.py`](../apps/billing/models.py), función `_license_secret_key_bytes()`). En **producción** con `DEBUG=False`, el secreto explícito es obligatorio.

### 2.2 Buenas prácticas

- No imprimir la llave en logs, trazas ni respuestas HTTP.
- No exponerla en formularios ni en el panel para usuarios finales.
- Tratar `.env` como secreto y restringir acceso al servidor.

---

## 3. Creación de suscripción para una compañía

Orden lógico recomendado:

1. **Compañía:** existe un registro en `Company` (módulo de compañías / admin).
2. **Plan:** existe un `Plan` en catálogo (o se crea uno nuevo).
3. **Suscripción:** crear `Subscription` vinculando:
   - **Compañía** (`OneToOne`: una suscripción por compañía).
   - **Plan** (`ForeignKey` con `PROTECT` sobre borrado de plan).
   - **`start_date`** y **`end_date`** (`DateField`).
   - Opcionalmente **`status`**, **`auto_renew`**, auditoría (`created_by` / `updated_by`).

4. **Guardar** mediante el ORM (`save()`), no solo SQL directo sobre fechas.

### 3.1 Qué hace el sistema al guardar

En cada `Subscription.save()`:

- Se recalcula **`integrity_signature`** con el secreto y las fechas (ver `generate_signature()` / `save()` en [`apps/billing/models.py`](../apps/billing/models.py)).
- Si la vigencia ya pasó y el estado era activo, puede sincronizarse a expirado (`_sync_status_with_end_date()`).

El usuario administrador **no introduce** la huella a mano: se genera automáticamente.

---

## 4. Contactos de soporte (`SubscriptionContact`)

Tras tener la suscripción:

1. Registrar contactos (hasta **3** por suscripción; validado en `clean()` del modelo).
2. Campos habituales: nombre completo, teléfono, correo (opcional pero sujeto a unicidad por suscripción si está informado), rol, notas.
3. Asociar cada contacto a la **`Subscription`** correspondiente (`ForeignKey`).

---

## 5. Validación en ejecución

Para decidir acceso, el servicio centralizado es **`evaluate_subscription_access(subscription)`** en [`apps/billing/services/license.py`](../apps/billing/services/license.py). La prioridad documentada es:

1. Firma inválida (`is_signature_valid()` / payload de `validate_license()`).
2. Vencimiento por fecha (`date.today() > end_date`).
3. Estado distinto de **activo** (`status != active`).

`Subscription.validate_license()` agrupa: `signature_valid`, `is_expired`, `status` y hasta tres contactos (útil para mensajes al usuario).

**Implementación de producto:** las pantallas de “integridad comprometida”, “licencia expirada” y la visualización de contactos deben **consumir** este resultado (middleware o vistas). Si aún no están cableadas en todas las rutas, el comportamiento de bloqueo sigue siendo el **diseño objetivo** descrito en [`CODAS_SUSCRIPCIONES_VALIDACION.md`](CODAS_SUSCRIPCIONES_VALIDACION.md).

---

## 6. Actualización de suscripción

- Cambios de **fechas**, **plan** (respetando `PROTECT`) u otros campos persistidos vía **`Subscription.save()`** recalculan **`integrity_signature`** y aplican la lógica de estado en `save()`.
- Evitar actualizar solo con **`QuerySet.update()`** o SQL directo sobre campos de vigencia sin recalcular la firma (ver comentarios en el modelo y en [`CODAS_SUSCRIPCIONES_VALIDACION.md`](CODAS_SUSCRIPCIONES_VALIDACION.md)). Si se usa `bulk_update`, usar **`refresh_integrity_signature()`** en memoria antes de persistir de forma coherente.

---

## 7. Restricciones operativas

| Restricción | Motivo |
|-------------|--------|
| No modificar `start_date` / `end_date` con SQL directo sin alinear la firma | La huella dejaría de coincidir con `is_signature_valid()`. |
| No usar `QuerySet.update()` sobre vigencia sin recalcular firma | Igual que arriba. |
| No rotar `LICENSE_SECRET_KEY` a la ligera en producción | Todas las firmas almacenadas quedarían inválidas salvo **migración controlada** (re-firmar filas o versionar el esquema). Acordar procedimiento antes de rotar. |
| No exponer `LICENSE_SECRET_KEY` en UI, logs ni repositorios | Comprometería la integridad del mecanismo. |

---

## 8. Resumen ejecutivo

| Concepto | Quién / cuándo |
|----------|----------------|
| `LICENSE_SECRET_KEY` | Una vez por entorno (operaciones / despliegue); entrada en `.env`, sin commitear. |
| `integrity_signature` | Automática en cada `save()` de `Subscription`; no la escribe el usuario. |
| Contactos | Hasta 3 por suscripción; asociados en `SubscriptionContact`. |
| Validación de acceso | `evaluate_subscription_access()` + reglas de negocio en vistas/middleware. |

---

*Documento operativo validado frente al repositorio CODAS. Ajustar si cambia el esquema de firma o la carga de settings.*
