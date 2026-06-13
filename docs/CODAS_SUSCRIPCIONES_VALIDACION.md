# CODAS — Validación del diseño de suscripciones y licenciamiento

**Fecha de revisión:** 2026-04-19  
**Alcance:** diseño propuesto (modelos `Subscription`, `SubscriptionContact`, `Payment`) frente al contexto del repositorio y buenas prácticas Django/seguridad.

**Código de referencia:** [`apps/company/models.py`](../apps/company/models.py) (`Company` con `name_short`, `name_long`). **Implementación propuesta:** app [`apps/billing`](../apps/billing/models.py) (`Plan`, `Subscription`, `SubscriptionContact`, `Payment`) y [`apps/billing/services/license.py`](../apps/billing/services/license.py).

---

## 1. Resumen ejecutivo

| Aspecto | Veredicto |
|---------|-----------|
| **Modelo de datos** | Coherente: `OneToOne` compañía–suscripción, pagos e historial, contactos para UX en bloqueo. |
| **Flujo `validate_license()`** | Útil para middleware/vistas: agrupa firma, vencimiento, estado y contactos. |
| **“Anti-manipulación” solo con BD** | **Parcialmente efectivo:** detecta cambios en fechas **si** no se recalcula la firma con el secreto. |
| **Protección frente a usuarios con acceso ORM/admin o al secreto** | **No sustituye** controles de autorización ni firma asimétrica; un actor con `LICENSE_SECRET_KEY` y escritura legítima puede fechas válidas y firma válida. |
| **Alineación con CODAS** | Ajustar nombres de campos (`name_short` vs `nameshort` en borradores), valorar `services/` para validación de licencia y campos de auditoría según [`.cursorrules`](../.cursorrules). |

---

## 2. Modelo `Subscription`

### 2.1 Función

Representar la licencia activa de la compañía (plan, vigencia, estado, renovación automática, huella de integridad). Encaja con el objetivo de negocio descrito.

### 2.2 Firma `integrity_signature` (SHA-256 sobre cadena con secreto)

**Qué sí cubre bien**

- Un cliente que **solo** altera `start_date` / `end_date` en SQL **sin** conocer `LICENSE_SECRET_KEY` no puede producir una firma válida; al validar, `is_signature_valid()` fallará.
- Restaurar una copia antigua de la BD puede dejar estados incoherentes; la firma ayuda a detectar inconsistencias si las fechas y la firma no cuadran.

**Limitaciones importantes (modelo de amenazas)**

1. **No es firma digital asimétrica:** es un digest con secreto compartido (similar a MAC). Quien tenga el **mismo secreto** que la app (p. ej. variable de entorno filtrada o servidor comprometido) puede recalcular y escribir fechas + firma coherentes.
2. **`save()` regenera siempre la firma:** cualquier guardado vía ORM con fechas nuevas produce firma **válida** para esas fechas. No impide que un **administrador autorizado** extienda la vigencia desde Django Admin o shell; solo ayuda frente a **tampering bruto en BD** sin el secreto.
3. **Operaciones que evitan `save()`:** `QuerySet.update()`, `bulk_update()`, SQL crudo pueden dejar `integrity_signature` desalineada. Hay que **documentar** que los cambios a fechas deben pasar por `Subscription.save()` o por un servicio que recalcule la firma explícitamente.
4. **Nombre “SHA256” vs “criptográfica”:** es integridad con secreto; para comunicación externa conviene hablar de **“huella de integridad con secreto”** o usar **HMAC-SHA256** (ver §5).

### 2.3 Expiración y estado

- Comparar `date.today() > end_date` es razonable para `DateField` **si** el criterio de negocio es “día calendario” en la zona horaria del despliegue.
- **Inconsistencia posible:** `status == "active"` pero ya vencida por fecha (o al revés). Conviene una regla explícita: p. ej. job o `save()` que sincronice `status`, o que `validate_license()` trate el vencimiento como bloqueo **independiente** del valor de `status` (documentado).
- `validate_license()` no devuelve un único “acceso permitido / denegado”; las vistas deben combinar `signature_valid`, `is_expired` y `status` con prioridad acordada (p. ej. firma inválida antes que “pendiente”).

### 2.4 Relaciones

- `OneToOneField(Company)`: correcto si una compañía tiene como máximo una suscripción “actual”. Si en el futuro se necesita **historial** de suscripciones por compañía, habría que pasar a `ForeignKey` + registro vigente o tabla de historial.
- `ForeignKey(Plan, on_delete=PROTECT)`: adecuado para no borrar planes referenciados.

---

## 3. Modelo `SubscriptionContact`

- Propósito (mostrar hasta 3 contactos en pantallas de error): alineado con el flujo descrito; `validate_license()` ya limita a `[:3]`.
- **Validaciones recomendadas en el diseño:** máximo 3 por suscripción, email/teléfono válidos, no duplicados — hoy son **requisitos de negocio**; en implementación conviene `clean()` / servicio de alta o restricción `UniqueConstraint` parcial por `(subscription, email)` (donde email no sea nulo), etc.

---

## 4. Modelo `Payment`

- Campos razonables para auditoría e integración futura con pasarelas.
- Las validaciones citadas (monto > 0, método en conjunto cerrado, suscripción existente y en estado aceptable) deben implementarse explícitamente (`validators`, `choices` en `method`, o capa `services/` al registrar pago).

---

## 5. Recomendaciones técnicas (al implementar)

1. **Preferir `hmac.new(secret, msg, hashlib.sha256).hexdigest()`** con mensaje canónico (p. ej. bytes UTF-8 de fechas en ISO fijo) frente a concatenar manualmente `fecha|fecha|secreto`; reduce ambigüedad y es el patrón habitual de integridad con secreto.
2. **Comparación constante en el tiempo** (opcional pero sana): `hmac.compare_digest(almacenado, calculado)` si en algún momento la firma se expone en canales sensibles a timing.
3. **Definir `LICENSE_SECRET_KEY` en settings** con longitud adecuada y rotación documentada; rotar implica **re-firmar** filas existentes o versionar el esquema de firma.
4. **Auditoría en modelos:** el proyecto sugiere `created_at` / `updated_at` y a veces `created_by` / `updated_by` donde aplique ([`.cursorrules`](../.cursorrules)); valorarlos en `Subscription` y `Payment`.
5. **Lógica de licencia en `services/`** (p. ej. `validate_subscription_for_company(company)`) para no duplicar reglas entre middleware, vistas y tareas programadas.
6. **Corregir borradores de `__str__`:** en este repo `Company` expone `name_short`, no `nameshort`.

---

## 6. Checklist de aceptación sugerido (implementación futura)

- [ ] Middleware o punto único de entrada que use el mismo criterio que `validate_license()` (o servicio equivalente).
- [ ] Tests: firma válida tras `save()`; fallo tras `UPDATE` directo de fechas sin firma; contactos máx. 3; pago con monto ≤ 0 rechazado.
- [ ] Política documentada para `bulk_update` / migraciones de datos masivos.
- [ ] Actualizar [`CODAS_MODELS.md`](CODAS_MODELS.md) y el diagrama ER cuando los modelos existan en código.

---

## 7. Conclusión

El diseño es **viable y claro** para gobernanza de vigencia, estado y UX de contacto ante errores. La firma con secreto aporta **detección de manipulación en BD** frente a atacantes **sin** el secreto de aplicación; no debe presentarse como protección absoluta frente a administradores de sistema, fugas del secreto o escritura vía ORM legítima. Completar con validaciones explícitas en `Payment`/`SubscriptionContact`, reglas de consistencia fecha–`status`, y capa de servicio única para decisiones de acceso.
