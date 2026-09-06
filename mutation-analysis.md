# Análisis de Mutation Testing — `src/payments_svc/refunds.py`

**Mutantes totales:** 46 · **Sobrevivientes:** 8 (17.39%)

---

### Mutante 1: ReplaceComparisonOperator_Eq_LtE

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceComparisonOperator_Eq_LtE |
| **Función** | `request_refund` |
| **Cambio** | `refund_amount == Decimal("0")` → `refund_amount <= Decimal("0")` (línea 44) |
| **Comportamiento sin cubrir** | Un `refund_amount` negativo ya no pasa por `validate_amount` (línea 51); se rechaza directamente en la línea 44 con razón genérica en vez de lanzar `AmountError`. |
| **Clasificación** | accionable |
| **Justificación** | Existe un camino observable diferente: un monto negativo produce `RefundDecision(REJECTED)` en vez de `AmountError`. El test no distingue entre ambos mecanismos de rechazo. |
| **¿Iterar?** | sí |

### Mutante 2: ReplaceComparisonOperator_Lt_Is

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceComparisonOperator_Lt_Is |
| **Función** | `validate_refunded_amount` |
| **Cambio** | `amount < Decimal("0")` → `amount is Decimal("0")` (línea 23) |
| **Comportamiento sin cubrir** | La validación de monto negativo se rompe completamente: `is` nunca es `True` para Decimals creados por_Value, así que montos negativos pasan sin error. |
| **Clasificación** | accionable |
| **Justificación** | La función ya no valida montos negativos. Si algún test invoca `validate_refunded_amount` con un valor negativo y espera `AmountError`, debería fallar; al sobrevivir, indica que no existe esa cobertura. |
| **¿Iterar?** | sí |

### Mutante 3: ReplaceComparisonOperator_LtE_Eq

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceComparisonOperator_LtE_Eq |
| **Función** | `request_refund` |
| **Cambio** | `remaining <= Decimal("0")` → `remaining == Decimal("0")` (línea 55) |
| **Comportamiento sin cubrir** | Si `remaining` fuera negativo (desbordamiento o datos inconsistentes), el rechazo no se activaría y se aprobaría un reembolso que no debería existir. |
| **Clasificación** | accionable |
| **Justificación** | El caso `remaining < 0` (distinto de `remaining == 0`) no está cubierto. Aunque en la práctica `remaining` no debería ser negativo, el código lo contempla con `<=` y un test debería reflejar esa intención. |
| **¿Iterar?** | sí |

### Mutante 4: ReplaceComparisonOperator_Is_Eq

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceComparisonOperator_Is_Eq |
| **Función** | `assert_refundable` |
| **Cambio** | `decision.status is RefundStatus.REJECTED` → `decision.status == RefundStatus.REJECTED` (línea 71) |
| **Comportamiento sin cubrir** | N/A |
| **Clasificación** | equivalente |
| **Justificación** | `RefundStatus` es `StrEnum`. Los miembros de StrEnum son singletons y `==` compara por valor, `is` por identidad. Para miembros de enum ambos producen el mismo resultado observable. |
| **¿Iterar?** | no |

### Mutante 5: ReplaceComparisonOperator_Is_LtE

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceComparisonOperator_Is_LtE |
| **Función** | `assert_refundable` |
| **Cambio** | `decision.status is RefundStatus.REJECTED` → `decision.status <= RefundStatus.REJECTED` (línea 71) |
| **Comportamiento sin cubrir** | `decision.status <= RefundStatus.REJECTED` es siempre `True` (tanto `"approved"` como `"rejected"` son `<= "rejected"` lexicográficamente). `assert_refundable` siempre lanza `AmountError`, incluso para reembolsos aprobados. |
| **Clasificación** | accionable |
| **Justificación** | Un test que invoque `assert_refundable` con un monto válido y espere que **no** lance excepción debería fallar. La ausencia de dicho test permite que este mutante sobreviva. |
| **¿Iterar?** | sí |

### Mutante 6: ReplaceComparisonOperator_Is_GtE

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceComparisonOperator_Is_GtE |
| **Función** | `assert_refundable` |
| **Cambio** | `decision.status is RefundStatus.REJECTED` → `decision.status >= RefundStatus.REJECTED` (línea 71) |
| **Comportamiento sin cubrir** | N/A |
| **Clasificación** | equivalente |
| **Justificación** | `"rejected" >= "rejected"` → `True` (lanza error, correcto). `"approved" >= "rejected"` → `False` (no lanza, correcto). El comportamiento es idéntico al original para ambos valores del enum. |
| **¿Iterar?** | no |

### Mutante 7: ReplaceTrueWithFalse

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceTrueWithFalse |
| **Función** | `RefundDecision` (dataclass) |
| **Cambio** | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` (línea 15) |
| **Comportamiento sin cubrir** | N/A |
| **Clasificación** | no accionable |
| **Justificación** | La inmutabilidad de la dataclass es una protección de diseño. Ningún test intenta mutar una instancia de `RefundDecision`, por lo que el cambio no tiene impacto observable en el comportamiento testeado. Cubrir esto implicaría testear la configuración de la dataclass, no el dominio. |
| **¿Iterar?** | no |

### Mutante 8: ReplaceOrWithAnd

| Campo | Valor |
| --- | --- |
| **Mutante** | ReplaceOrWithAnd |
| **Función** | `assert_refundable` |
| **Cambio** | `decision.reason or "refund rejected"` → `decision.reason and "refund rejected"` (línea 72) |
| **Comportamiento sin cubrir** | Con `and`, si `reason` es `None` (reembolso aprobado), retorna `None` en vez de `"refund rejected"`. Si `reason` es un string no vacío, retorna `"refund rejected"` en vez de la razón original. El mensaje de error cambia. |
| **Clasificación** | accionable |
| **Justificación** | Un test que verifique el contenido del mensaje de `AmountError` lanzado por `assert_refundable` debería distinguir entre la razón específica y el fallback genérico. Al sobrevivir, indica que no se validan los mensajes de error. |
| **¿Iterar?** | sí |


## Resumen de clasificación

| Clasificación | Cantidad | Mutantes |
|---|---|---|
| **Accionable** | 5 | Eq_LtE, Lt_Is, LtE_Eq, Is_LtE, OrWithAnd |
| **Equivalente** | 2 | Is_Eq, Is_GtE |
| **No accionable** | 1 | TrueWithFalse |
| **Pendiente** | 0 | — |

**Total analizados:** 8 · **Accionables para iterar:** 5 · **Justificados sin test:** 3
