# Auditoría — `src/payments_svc/legacy/settlement.py`

Alcance: solo el archivo entregado. Cada hallazgo cita líneas reales. No se proponen correcciones en esta fase.

Contexto: tour técnico en `settlement-tour.md`.

---

## H-01 — La moneda de liquidación del comercio se ignora

- **Categoría:** lógica de negocio / consistencia de datos
- **Severidad:** Alta (condicional a la intención; ver paso de validación)
- **Líneas:** 14 (definición), 132 (uso de moneda)
- **Evidencia:** `Merchant.settlement_currency` se declara en la línea 14 y **no se lee en ninguna parte del archivo** (verificado con búsqueda: solo aparece la declaración). La línea de salida fija `currency=target_currency` (132), y todos los montos se convierten a `target_currency` (90–107). `settlement_currency` no interviene.
- **Riesgo concreto:** si cada comercio debe liquidarse en su propia moneda, el reporte liquida a todos en `target_currency` (default `"USD"`, línea 83). Un comercio cuya `settlement_currency` sea distinta recibiría un monto en la divisa equivocada.
- **Siguiente paso verificable:** confirmar con el dominio si `settlement_currency` es contractual. Prueba: construir un `Merchant` con `settlement_currency="EUR"` y `target_currency="USD"` y verificar que hoy la línea sale en USD; si el esperado es EUR → fallo demostrable.

---

## H-02 — Escala de redondeo fija a 2 decimales para cualquier moneda

- **Categoría:** precisión monetaria
- **Severidad:** Media
- **Líneas:** 188–189 (y afecta 126–131, 140–145)
- **Evidencia:** `round_money` cuantiza siempre con `Decimal("0.01")` (189), independientemente de `target_currency` (parámetro libre, línea 83).
- **Riesgo concreto:** monedas sin decimales (p. ej. `JPY`) o con 3 (p. ej. `KWD`) quedan con una precisión incorrecta: se conservan/producen centavos inexistentes y los totales pueden no cuadrar con el sistema de pago.
- **Siguiente paso verificable:** prueba con `target_currency="JPY"` y `"KWD"`; comparar el número de decimales de `SettlementLine`/totales contra el estándar de cada divisa.

---

## H-03 — Comparación de monedas sensible a mayúsculas

- **Categoría:** robustez / integración
- **Severidad:** Media
- **Líneas:** 183–185
- **Evidencia:** `if source == target:` es una comparación de cadenas exacta y sensible a mayúsculas. No hay normalización de `batch.currency`, `target_currency` ni del `source="USD"` de ajustes.
- **Riesgo concreto:** con `source="usd"` y `target="USD"` se toma la rama FX y se llama a `fx_rates.convert(..., "usd", "USD")`, que puede fallar (tasa inexistente / excepción) o devolver una conversión espuria cuando en realidad la moneda es la misma.
- **Siguiente paso verificable:** probar `convert_money` con `source="usd"`, `target="USD"` y verificar si se invoca `fx_rates.convert` (fallo demostrable si el doble devuelve error).

---

## H-04 — Los ajustes manuales se asumen siempre en USD

- **Categoría:** lógica de negocio / precisión
- **Severidad:** Media
- **Líneas:** 156–164 (constante en 162)
- **Evidencia:** en `calculate_adjustment_total` cada `adjustment.amount` se convierte con `source="USD"` fijo (162). `SettlementAdjustment` no tiene campo de moneda (líneas 27–31).
- **Riesgo concreto:** si un ajuste viene en la moneda del comercio y no en USD, el monto se convierte desde una divisa incorrecta; el `adjustment_amount` de la línea (129) queda mal.
- **Siguiente paso verificable:** confirmar la moneda de origen de los ajustes con el dominio; prueba: ajuste nominal pensado en otra divisa y comparar contra el valor esperado.

---

## H-05 — Patrón N+1 de acceso al repositorio dentro del bucle

- **Categoría:** rendimiento
- **Severidad:** Media
- **Líneas:** 88–89 (loop + `load_payment_batch`), 108–114 → 156 (`load_manual_adjustments`)
- **Evidencia:** por cada `merchant` (88) se llama `repository.load_payment_batch` (89) y `calculate_adjustment_total` → `repository.load_manual_adjustments` (156). No hay carga por lote.
- **Riesgo concreto:** el número de viajes al repositorio crece como `1 + 2N`; con muchos comercios el tiempo de settlement escala linealmente en IO, no en cómputo.
- **Siguiente paso verificable:** instrumentar/contar llamadas con un repositorio falso y `N` comercios; medir tiempo con `N` creciente para confirmar el crecimiento.

---

## H-06 — `reserve_rate` no se valida y la reserva puede volverse negativa o excesiva

- **Categoría:** integridad de negocio
- **Severidad:** Media
- **Líneas:** 118 (uso), 168–174 (cálculo)
- **Evidencia:** `calculate_reserve_amount` protege solo la base (`max(gross - refund, 0)`, 173), pero multiplica directamente por `reserve_rate` sin acotar el rango. `merchant.reserve_rate` es un `Decimal` de entrada sin validación visible.
- **Riesgo concreto:** con `reserve_rate > 1` la reserva supera el monto elegible; con `reserve_rate` negativo la reserva es negativa y **aumenta** el `net_amount` (121). En ambos casos el resultado es un monto de liquidación incorrecto sin señal de error.
- **Siguiente paso verificable:** prueba con `reserve_rate=1.5` y con `reserve_rate=-0.1`; observar `reserve_amount` y `net_amount` resultantes.

---

## H-07 — `net_amount` puede ser negativo y no hay manejo ni marca de ello

- **Categoría:** lógica de negocio / límites
- **Severidad:** Baja
- **Líneas:** 120–121
- **Evidencia:** `net_amount = gross - fee - refund + adjustment - reserve` sin cota inferior ni indicador de estado.
- **Riesgo concreto:** con `fee + refund + reserve > gross + adjustment`, la línea y `total_net` (145) salen negativas; si el consumidor no admite netos negativos, el settlement queda inconsistente (no confirmable en el archivo).
- **Siguiente paso verificable:** prueba con `gross=10`, `fee=8`, `refund=8` (o `reserve_rate` alto) y verificar el signo de `net_amount`; confirmar con dominio si es válido.

---

## H-08 — Redondeo por ítem antes de agregar (posible deriva de redondeo)

- **Categoría:** precisión monetaria
- **Severidad:** Baja
- **Líneas:** 159–164 (ajustes), 183–185 (`convert_money`)
- **Evidencia:** `convert_money` redondea a centavos **cada** conversión (184–185); en los ajustes se redondea ítem por ítem y luego el total (165). Igual para `gross/fee/refund` individuales (90–107).
- **Riesgo concreto:** el resultado puede diferir del que se obtendría convirtiendo/agregando con precisión completa y redondeando al final (diferencia de centavos). Relevante si se contrasta contra otra fuente de verdad contable.
- **Siguiente paso verificable:** prueba de propiedad comparando `sum(convertido_i)` vs `convertir(sum_i)` para conjuntos de importes con muchos decimales; medir la magnitud de la deriva.

---

## H-09 — Campos declarados y nunca usados / falta de validación cruzada del batch

- **Categoría:** limpieza / integridad
- **Severidad:** Baja
- **Líneas:** 12 (`country`), 20 (`PaymentBatch.merchant_id`), 31 (`reason`)
- **Evidencia:** `Merchant.country` (12) y `SettlementAdjustment.reason` (31) no se leen en el archivo. `PaymentBatch.merchant_id` (20) tampoco se usa: en el bucle se pasa `merchant.id` a `load_payment_batch` (89) y se confía en el resultado sin comprobar que `batch.merchant_id == merchant.id`.
- **Riesgo concreto:** un repositorio que devuelva el batch de otro comercio (o un `reason`/`country` que se esperaba influir en el cálculo) pasa silenciosamente; además son campos muertos que sugieren lógica incompleta.
- **Siguiente paso verificable:** prueba con un repositorio falso que devuelva un `batch.merchant_id` distinto al solicitado y verificar que hoy no se detecta.

---

## Verificado y descartado (para evitar falsos positivos)

- **Reconciliación de totales (líneas 120–146):** comprobé que `gross/fee/refund` (90–107), `adjustment_amount` (165) y `reserve_amount` (174) ya salen redondeados de sus funciones; por tanto `net_amount` (120–121) y los totales con `sum_money` **cuadran exactamente**. No se reporta inconsistencia de cuadre.

## Orden sugerido de verificación

H-01 → H-04 (riesgo de importe incorrecto), luego H-02/H-03 (robustez/precisión), después H-05/H-06 (integridad/rendimiento) y H-07..H-09 (borde/limpieza).
