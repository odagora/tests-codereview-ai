# Code Review — Diff `develop...HEAD`

## Resumen de cambios

Nuevo endpoint `POST /accounts/{account_id}/manual-refunds` y modelo `ManualRefundRequest` en `src/payments_svc/api.py`.

---

## 1. Corrección — Hallazgos

### [Alta] `src/payments_svc/api.py:103-104` — `Decimal()` en vez de `parse_amount()`

```python
original_amount=Decimal(payload.original_amount),
refund_amount=Decimal(payload.refund_amount),
```

`Decimal()` lanza `decimal.InvalidOperation` para inputs como `"not-money"`, pero el `except` solo captura `AmountError`. Un input inválido causa **500 Internal Server Error** en vez de 400.

```python
# Línea 106 — solo captura AmountError
except AmountError as exc:
```

La función `create_refund` (línea 77-81) usa `parse_amount()` que valida floats, strings vacíos, y convierte todo a `AmountError`. `create_manual_refund` no lo hace.

**Corrección:** Reemplazar `Decimal(payload.original_amount)` por `parse_amount(payload.original_amount)` (y lo mismo para `refund_amount`).

---

### [Alta] `src/payments_svc/api.py:112` — REJECTED retorna 200 en vez de 400

```python
reason=payload.reason or decision.reason,
```

Cuando `request_refund` retorna `status=REJECTED` (ej: "refund exceeds refundable amount"), `create_refund` lanza `HTTPException(400)` (líneas 85-87). Pero `create_manual_refund` retorna 200 con `status="rejected"` sin verificar el estado. Esto rompe el contrato de la API: los rechazos deben ser errores HTTP.

Además, `payload.reason or decision.reason` sobreescribe la razón del rechazo con un valor arbitrario del usuario, ocultando por qué falló.

**Corrección:** Agregar la misma lógica de status check que tiene `create_refund`:

```python
status_code = 200 if decision.status == RefundStatus.APPROVED else 400
if status_code >= 400:
    raise HTTPException(status_code=status_code, detail=decision.reason)
```

---

### [Media] `src/payments_svc/api.py:42` — `already_refunded` está en el modelo pero nunca se usa

`ManualRefundRequest` declara `already_refunded: str = "0.00"` pero el endpoint nunca lo pasa a `request_refund`. Si un cliente lo envía, se ignora silenciosamente y el refund se calcula como si no hubiera reembolsos previos.

**Corrección:** Si es intencional (manual refunds siempre son desde cero), eliminar el campo del modelo. Si no lo es, pasar `already_refunded=parse_amount(payload.already_refunded)` a `request_refund`.

---

## 2. Seguridad — Hallazgos

### [Alta] `src/payments_svc/api.py:97-98` — `account_id` no se valida ni se usa

El parámetro `account_id` es parte de la URL pero se ignora completamente en la lógica del endpoint. No hay verificación de que el llamador tenga autorización sobre esa cuenta. Un usuario podría crear reembolsos para cuentas ajenas.

**Corrección:** Al menos loguear o validar el `account_id` contra un contexto de autorización. Si es un stub temporal, documentarlo explícitamente.

---

## 3. Rendimiento — Sin hallazgos

No se introduce trabajo costoso ni complejidad innecesaria en rutas calientes.

---

## 4. Tests faltantes — Hallazgos

### [Media] `tests/test_api.py` — No hay tests para `create_manual_refund`

Los tests existentes solo cubren `create_payment` y `create_refund`. El nuevo endpoint no tiene cobertura. Faltan casos como:
- Happy path (aprobado)
- Input inválido (`"not-money"`) — que actualmente causa 500
- Rechazo por exceder monto reembolsable
- `reason` provisto vs. omitido

**Corrección:** Agregar tests al menos para el happy path y el caso de input inválido, replicando el patrón de `test_create_refund_*`.

---

## 5. Estilo — Sin hallazgos

Los nombres y legibilidad del código nuevo son consistentes con el resto del archivo.

---

## 6. Documentación — Hallazgos

### [Baja] No hay docstring ni tag de OpenAPI para distinguir el nuevo endpoint de `/refunds`

Un consumidor no puede saber cuándo usar uno u otro.

**Corrección:** Agregar `summary` y `description` al decorador `@app.post(...)` para documentar la diferencia entre refunds automáticos y manuales.
