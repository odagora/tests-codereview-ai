# Tour técnico — `src/payments_svc/legacy/settlement.py`

## 1. Responsabilidad principal del módulo

**Evidencia:** El módulo construye un reporte de liquidación (*settlement*) agregando, por comercio, montos brutos, comisiones, reembolsos y ajustes en una moneda destino, aplicando conversión de divisas y retención de reserva. El punto de entrada es `build_settlement_report(...)` (línea 79), que devuelve un `SettlementReport` (línea 47).

Define además:
- Modelos de datos inmutables: `Merchant`, `PaymentBatch`, `SettlementAdjustment`, `SettlementLine`, `SettlementReport` (líneas 10–56).
- Dos contratos (Protocols): `SettlementRepository` (59) y `FxRates` (74).
- Helpers puros de dinero/negocio: `calculate_adjustment_total` (149), `calculate_reserve_amount` (168), `convert_money` (177), `round_money` (188), `sum_money` (192).

**Inferencia:** La lógica se concentra en el cálculo de `net_amount` (líneas 120–121), por lo que el módulo parece ser el núcleo del cálculo de liquidación, no una capa de persistencia ni de transporte.

## 2. Entradas y su origen

**Evidencia:**
- Parámetros directos de `build_settlement_report`: `settlement_date: date`, `repository: SettlementRepository`, `fx_rates: FxRates`, `target_currency: str = "USD"` (líneas 79–84).
- Datos del repositorio:
  - `list_merchants_for_settlement(settlement_date)` → `list[Merchant]` (línea 85).
  - `load_payment_batch(merchant_id, settlement_date)` → `PaymentBatch` (línea 89).
  - `load_manual_adjustments(merchant_id, settlement_date)` → `list[SettlementAdjustment]` (línea 156).
- Conversión de divisas vía `fx_rates.convert(...)` (línea 185).

**Inferencia:** El origen concreto (DB, API, archivos, cola) no es visible; solo se conoce a través de las interfaces `SettlementRepository` y `FxRates`. El origen de `settlement_date` y `target_currency` tampoco se ve en el archivo (probablemente el llamador).

## 3. Salidas y consumidores

**Evidencia:**
- `build_settlement_report` retorna un `SettlementReport` con `lines: tuple[SettlementLine, ...]` y totales agregados (líneas 136–146).
- Los helpers retornan `Decimal` (`calculate_adjustment_total`, `calculate_reserve_amount`, `convert_money`, `round_money`, `sum_money`).

**Inferencia:** No hay consumidores visibles en el archivo. El reporte probablemente se serializa y se envía a un proceso posterior de pago/reporte, pero eso no está en el código entregado.

## 4. Dependencias

**Internas (dentro del módulo):**
- `build_settlement_report` usa `convert_money`, `calculate_adjustment_total`, `calculate_reserve_amount`, `round_money`, `sum_money` (líneas 90–145).
- `calculate_adjustment_total` usa `convert_money` y `round_money` (159–165).
- `build_settlement_report` retorna entidades definidas en el propio módulo.

**Externas (biblioteca estándar únicamente):**
- `__future__.annotations` (1)
- `dataclasses.dataclass` (3)
- `datetime.date` (4)
- `decimal.Decimal`, `decimal.ROUND_HALF_UP` (5)
- `collections.abc.Iterable` (6)
- `typing.Protocol` (7)

**Inferencia:** No hay dependencias de terceros ni imports del resto del paquete `payments_svc`; el acoplamiento con infraestructura se hace vía inyección de dependencias (Protocols).

## 5. Flujo principal paso a paso (por `build_settlement_report`)

1. Obtiene los comercios a liquidar: `repository.list_merchants_for_settlement(settlement_date)` (85).
2. Itera cada `merchant` (88).
3. Carga el batch de pagos del comercio (89).
4. Convierte `gross_amount`, `fee_amount` y `refund_amount` a `target_currency` con `convert_money` (90–107).
5. Calcula el total de ajustes manuales (conversión incluida) con `calculate_adjustment_total` (108–114).
6. Calcula la reserva: `eligible = max(gross - refund, 0)`, multiplicado por `reserve_rate` (115–119, 168–174).
7. Calcula `net_amount = gross - fee - refund + adjustment - reserve` (120–121).
8. Crea un `SettlementLine` redondeando cada componente (123–134) y lo agrega a `lines` (123).
9. Tras el bucle, suma cada columna con `sum_money` y arma el `SettlementReport` (136–146).

**Detalle de `calculate_adjustment_total`:** carga ajustes (156), acumula cada uno convertido desde `"USD"` fijo hacia `target_currency` (158–164), redondea el total (165).

**Detalle de `convert_money`:** si `source == target` redondea sin llamar FX; si no, delega en `fx_rates.convert` (183–185).

## 6. Supuestos / datos no confirmables con el código

**Inferencia (no evidenciable):**
- Que `Merchant.reserve_rate` es una fracción (p. ej. `0.10`) y no un porcentaje (`10`), consistente con `eligible * reserve_rate`.
- Que `PaymentBatch.currency` es la moneda de origen de los montos y `Merchant.settlement_currency` no se usa en este flujo (no aparece referenciada).
- Que los ajustes siempre vienen denominados en `"USD"` (hardcodeado en la línea 162).
- Que `settlement_date` es la fecha correcta tanto para batch como para ajustes (se pasa igual a ambos).
- Que el repositorio es síncrono y no lanza excepciones para comercios sin batch/ajustes.
- Que la convención de redondeo `ROUND_HALF_UP` y la escala `0.01` son las correctas para todas las monedas destino.
- Que la relación entre `net_amount` visible y el monto efectivamente liquidado no tiene pasos intermedios fuera del módulo.

## Punto de control (a confirmar por un humano)

1. ¿El origen real de `settlement_date` y `target_currency` está en el llamador y cuál es?
2. ¿Un ajuste puede venir en moneda distinta de USD? (la moneda está fija en la línea 162).
3. ¿`reserve_rate` es fracción o porcentaje?
4. ¿Para qué existe `Merchant.settlement_currency` si no se usa aquí?
5. ¿Qué consumidor recibe el `SettlementReport` y qué formato espera?
6. ¿`PaymentBatch.currency` es siempre la moneda de `gross/fee/refund`?
7. ¿Hay reglas de redondeo por moneda o todas usan 2 decimales con `ROUND_HALF_UP`?
8. ¿Se esperan comercios sin batch o sin ajustes, y cómo responde el repositorio?
