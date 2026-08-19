# Modos de Falla en amounts.py

Catálogo de fallos en el módulo de cálculo de montos y tarifas. **No se asume que la implementación actual es correcta.**

## FRONTERA

### F001 | Cantidad en el límite superior
- **ID:** F001
- **Categoría:** Frontera / Validación de rango
- **Riesgo:** Transacciones rechazadas legítimamente en el límite
- **Entrada que lo desestima:** amount = 100000.00 (exacto), amount = 100000.01 (excede)
- **Comportamiento actual observado en el código:** `validate_amount()` rechaza si `amount > MAX_AMOUNT` (línea 64). Permite exactamente 100000.00
- **Contrato esperado recomendado:** MAX_AMOUNT = 100000.00 debería permitir exactamente 100000.00. Actual: inclusivo ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Define el techo de una transacción. Un off-by-one rechaza o permite inesperadamente

### F002 | Cantidad negativa
- **ID:** F002
- **Categoría:** Frontera / Validación de rango
- **Riesgo:** Permitir reembolsos sin control
- **Entrada que lo desestima:** amount = -0.01, amount = Decimal("-100")
- **Comportamiento actual observado en el código:** `validate_amount()` rechaza si `amount < Decimal("0")` (línea 61)
- **Contrato esperado recomendado:** Cantidades negativas inválidas en pagos forward. Si existen reembolsos, necesitan función separada
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Un dólar negativo es reembolso disfrazado. Sin control, representa riesgo

### F003 | Cantidad cero
- **ID:** F003
- **Categoría:** Frontera / Caso especial
- **Riesgo:** Transacciones sin movimiento de dinero; ambigüedad en modelo
- **Entrada que lo desestima:** amount = Decimal("0"), amount = Decimal("0.00")
- **Comportamiento actual observado en el código:** Válido. `calculate_fee()` retorna 0.00 para amount == 0 (línea 76-77)
- **Contrato esperado recomendado:** **Pendiente de decisión.** ¿Transacción de $0 tiene sentido (diferido, registro vacío)? ¿O debe rechazarse?
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** Pago de $0 es ambiguo: ¿incompleto, test, reparación de datos? Afecta auditoría

### F004 | Redondeo en frontera (0.005, 0.015)
- **ID:** F004
- **Categoría:** Frontera / Precisión decimal
- **Riesgo:** Centavos faltantes tras cálculo de fee
- **Entrada que lo desestima:** fee = Decimal("0.005"), fee = Decimal("0.015")
- **Comportamiento actual observado en el código:** `round_money()` usa ROUND_HALF_EVEN. 0.005 → 0.00, 0.015 → 0.02 (redondeo bancario)
- **Contrato esperado recomendado:** ROUND_HALF_EVEN es estándar. Comportamiento predecible ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Cada centavo cuenta. Redondeo incorrecto = pérdida o confusión en reconciliación

### F005 | Fee mínimo excede la cantidad original
- **ID:** F005
- **Categoría:** Frontera / Lógica de negocio
- **Riesgo:** Total final invierte economía de transacción
- **Entrada que lo desestima:** amount = Decimal("0.10"), currency = "USD" → fee mín = $0.30, total = $0.40 (4x)
- **Comportamiento actual observado en el código:** `calculate_fee()` aplica `max(percentage_fee, MINIMUM_FEES[currency])` (línea 80). Mínimo ganará siempre para montos pequeños
- **Contrato esperado recomendado:** **Pendiente de decisión.** ¿Fee > amount es aceptable? Podría ser:
  1. Intencional: "no procesamos pagos pequeños"
  2. Error: mínimo debería reajustarse
  3. Especial: rechazar montos < X antes de calcular fee
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** Define viabilidad de micropagos. Fee > monto es inaceptable para usuario

## EQUIVALENCIA

### E001 | Tipos de entrada en parse_amount
- **ID:** E001
- **Categoría:** Equivalencia / Polimorfismo
- **Riesgo:** Comportamiento inconsistente entre tipos equivalentes
- **Entrada que lo desestima:** parse_amount(100), parse_amount(100.0), parse_amount("100"), parse_amount(Decimal("100"))
- **Comportamiento actual observado en el código:** Todos convierten a `Decimal(str(raw).strip())` (línea 36). Evita pérdida de float ✓
- **Contrato esperado recomendado:** Conversión vía string previene pérdida de precisión de float. Actual correcto ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Python floats pierden precisión. $100.50 como float != $100.50 exacto

### E002 | Monedas equivalentes (mayúsculas, espacios)
- **ID:** E002
- **Categoría:** Equivalencia / Normalización
- **Riesgo:** Rechazo de monedas válidas por variación cosmética
- **Entrada que lo desestima:** currency = "usd", currency = "USD ", currency = "  USD  "
- **Comportamiento actual observado en el código:** `normalize_currency()` hace `strip().upper()` (línea 50) ✓
- **Contrato esperado recomendado:** Aceptar monedas en cualquier caso y espacios. Actual cumple ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** UX: rechazar "usd" minúscula previene errores del cliente

### E003 | Punto decimal vs coma regional
- **ID:** E003
- **Categoría:** Equivalencia / Formato regional
- **Riesgo:** Rechazo o misparsing de formatos locales
- **Entrada que lo desestima:** parse_amount("100,50") (formato europeo)
- **Comportamiento actual observado en el código:** Cero manejo de coma. "100,50" → InvalidOperation → AmountError
- **Contrato esperado recomendado:** **Pendiente de decisión.** ¿Soportar coma decimal? Esperado en EUR/COP. Actual: rechaza, fuerza punto
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** Usuarios europeos envían "100,50" naturalmente. Rechazar = mala UX

## NULL / VACÍO

### N001 | amount es None
- **ID:** N001
- **Categoría:** Null / Requerido
- **Riesgo:** Crash o bypass de validación
- **Entrada que lo desestima:** raw = None
- **Comportamiento actual observado en el código:** Verifica `if raw is None` (línea 32) y levanta AmountError ✓
- **Contrato esperado recomendado:** amount obligatorio, rechazo correcto ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Cantidad ausente es irreconciliable

### N002 | currency es None
- **ID:** N002
- **Categoría:** Null / Requerido
- **Riesgo:** KeyError al acceder FEE_RATES[currency]
- **Entrada que lo desestima:** currency = None
- **Comportamiento actual observado en el código:** Verifica `if currency is None` (línea 47) y levanta CurrencyError ✓
- **Contrato esperado recomendado:** currency obligatorio, rechazo correcto ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Sin moneda, no se calcula fee ni se valida monto

### N003 | currency es cadena vacía
- **ID:** N003
- **Categoría:** Null / Vacío
- **Riesgo:** Rechazo tras normalización
- **Entrada que lo desestima:** currency = "", currency = "   "
- **Comportamiento actual observado en el código:** `strip()` detecta `if not normalized` (línea 51) y levanta CurrencyError ✓
- **Contrato esperado recomendado:** Cadenas vacías = None. Rechazo correcto ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** Distingue "no especificada" vs "especificada vacía"

### N004 | parse_amount recibe cadena vacía
- **ID:** N004
- **Categoría:** Null / Vacío
- **Riesgo:** Mensaje de error genérico en caso especial
- **Entrada que lo desestima:** raw = "", raw = "   "
- **Comportamiento actual observado en el código:** `Decimal("")` → InvalidOperation → AmountError("amount must be numeric")
- **Contrato esperado recomendado:** Rechaza correctamente, pero mensaje debería ser "amount is required" para claridad
- **Estado del contrato:** confirmado (rechaza, mejora en mensajes)
- **Por qué importa para pagos:** Claridad: "requerido" vs "formato inválido" son errores distintos

## CONTRATO

### C001 | total_with_fee no normaliza currency
- **ID:** C001
- **Categoría:** Contrato / Coherencia
- **Riesgo:** Silenciar error de currency inválida según flujo
- **Entrada que lo desestima:** total_with_fee(Decimal("100"), "INVALID_CURRENCY")
- **Comportamiento actual observado en el código:** `total_with_fee()` valida amount pero NO currency. `calculate_fee()` la normaliza (línea 73)
- **Contrato esperado recomendado:** **Pendiente de decisión.** ¿total_with_fee debe validar currency temprano? ¿O asumirla válida (propagando error de calculate_fee)?
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** Contrato de función confuso. Afecta testing y debugging

### C002 | round_money sin validación de entrada
- **ID:** C002
- **Categoría:** Contrato / Precondición
- **Riesgo:** NaN/Infinito propagan sin error
- **Entrada que lo desestima:** round_money(Decimal("Infinity")), round_money(Decimal("NaN"))
- **Comportamiento actual observado en el código:** `quantize()` sin check de finitud. Infinito/NaN se propagan silenciosamente
- **Contrato esperado recomendado:** **Pendiente de decisión.** ¿round_money rechaza infinito/NaN? Actual: silencia. Mejor: levantar AmountError si no finito
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** Fee calculada como Infinity es dato corrupto que entra silenciosamente en reconciliación

### C003 | Moneda validada pero faltante en fee tables
- **ID:** C003
- **Categoría:** Contrato / Integridad
- **Riesgo:** KeyError si FEE_RATES/MINIMUM_FEES desincronizados
- **Entrada que lo desestima:** Moneda normalizada pero ausente en uno de los dicts
- **Comportamiento actual observado en el código:** `normalize_currency()` valida contra FEE_RATES (línea 54). Acceso a MINIMUM_FEES sin assert (línea 80)
- **Contrato esperado recomendado:** FEE_RATES y MINIMUM_FEES deben tener exactamente las mismas claves. Debería haber assert al inicio del módulo
- **Estado del contrato:** confirmado como riesgo
- **Por qué importa para pagos:** Error de configuración silencioso causa crashes en produción para moneda aparentemente soportada

### C004 | Cantidad negativa Decimal("-0")
- **ID:** C004
- **Categoría:** Contrato / Casos extremos
- **Riesgo:** Ambigüedad: -0 == 0 pero simboliza diferente intención
- **Entrada que lo desestima:** amount = Decimal("-0"), parse_amount("-0.00")
- **Comportamiento actual observado en el código:** `validate_amount()` comprueba `< Decimal("0")`. Decimal("-0") < 0 es False. Se permite ✓
- **Contrato esperado recomendado:** -0 === 0 matemáticamente. Permitir es correcto ✓
- **Estado del contrato:** confirmado
- **Por qué importa para pagos:** -0 vs 0 sin diferencia práctica. Documentar para claridad

### C005 | Precision: redondeo post-suma puede exceder MAX_AMOUNT
- **ID:** C005
- **Categoría:** Contrato / Precisión
- **Riesgo:** total_with_fee puede violar máximo después de redondeo
- **Entrada que lo desestima:** amount = Decimal("99999.996"), currency = "USD" → suma fee → redondea a 100000.00+ (excede 100000.00)
- **Comportamiento actual observado en el código:** Valida amount primero, luego suma fee y redondea. Montos edge pueden salir de rango post-redondeo
- **Contrato esperado recomendado:** **Pendiente de decisión.** ¿Redondear antes de sumar? ¿Validar post-suma? Actual: silencia el problema
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** total_with_fee que produce 100000.01 viola máximo permitido. Bug silencioso en edge

### C006 | FEE_RATES y MINIMUM_FEES desincronizados
- **ID:** C006
- **Categoría:** Contrato / Integridad de datos
- **Riesgo:** KeyError si dicts tienen claves distintas
- **Entrada que lo desestima:** Moneda en FEE_RATES pero no en MINIMUM_FEES (ej: código de mantenimiento)
- **Comportamiento actual observado en el código:** `calculate_fee()` accede ambos sin assert (línea 79, 80)
- **Contrato esperado recomendado:** Debería haber validación: `assert set(FEE_RATES.keys()) == set(MINIMUM_FEES.keys())` al módulo init
- **Estado del contrato:** pendiente de decisión
- **Por qué importa para pagos:** Error de configuración silencioso causa crash para moneda aparentemente válida
