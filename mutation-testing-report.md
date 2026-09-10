# Mutation Testing — Análisis Comparativo

## Tabla resumen

| Suite | Mutantes totales | Sobrevivientes | Tasa de mortalidad | Reducción vs anterior |
|-------|------------------|----------------|--------------------|-----------------------|
| Ingenua | 46 | 10 | 78.26% | — |
| Original | 46 | 8 | 82.61% | 2 mutantes eliminados |
| Mata-mutantes | 46 | 4 | 91.30% | 4 mutantes eliminados |

---

## Análisis de tendencia

### Transición Ingenua → Original (10 → 8 sobrevivientes)

**2 mutantes eliminados:**
- `Eq → Lt` (reemplazar `==` por `<`)
- `Eq → Is` (reemplazar `==` por `is`)

**Tipo de mutante muerto:** Comparaciones de igualdad (`Eq`) donde el valor límite probablemente es 0 o un entero, haciendo que `==0` y `<0` se comporten idénticamente en el contexto de montos. Los tests originales ya cubrían estos bordes.

**Huecos que persisten:** 6 comparadores (`Eq→LtE`, `Lt→Is`, `LtE→Eq`, `Is→Eq`, `Is→LtE`, `Is→GtE`) + `ReplaceTrueWithFalse` + `ReplaceOrWithAnd`.

---

### Transición Original → Mata-mutantes (8 → 4 sobrevivientes)

**4 mutantes eliminados:**
- `Eq → LtE`
- `Lt → Is`
- `LtE → Eq`
- `Is → LtE`

**Tipo de mutante muerto:** Operadores de comparación entre tipos numéricos y `None`/`bool`. Al agregar tests que verifican que el código rechaza entradas no numéricas (e.g., `None`), se mata `Is → LtE` y `Lt → Is`. Los tests que validan que `0.00` no es un monto válido eliminan `Eq → LtE` y `LtE → Eq`.

**Huecos que persisten:** Solo 4 mutantes residuales, todos en categorías difíciles.

---

## Los 4 sobrevivientes finales y por qué resisten

| Mutante | Por qué sobrevive |
|---------|-------------------|
| `Is → Eq` | Python distingue `is` de `==` para `None`; el test suite probablemente no tiene un caso donde `None` sea pasado como argumento, o `==None` se comporta igual que `is None` para enteros/floats |
| `Is → GtE` | Similar: `is` vs `>=` para un objeto `None`. Si el código nunca recibe `None`, la mutación no cambia el resultado |
| `ReplaceTrueWithFalse` | El test suite no tiene un caso que ejecute la rama donde `True` es devuelto directamente (ej: early return de éxito). Solo se testean los caminos de error |
| `ReplaceOrWithAnd` | El test suite no cubre la combinación de condiciones donde `or` vs `and` produzca resultados distintos. Probablemente un guard clause con múltiples condiciones donde solo una rama se ejecuta en los tests |

---

## Conclusión

El esfuerzo de iteración **sí justificó la reducción**: pasar de 78.26% a 91.30% de mortalidad (+13 puntos) eliminando 6 sobrevivientes en 2 rondas. Los 4 mutantes restantes son inherentemente difíciles de matar porque involucran **`is` vs `==` para `None`** (comportamiento idéntico cuando el código nunca recibe `None`), **`True` hardcodeado en early returns** (la rama de éxito nunca se asertiza explícitamente), y **`or` vs `and` en guard clauses** donde solo una condición se activa en los tests. Para llegar a 100% habría que agregar: un test que pase `None` explícitamente, un test que verifique el return de éxito, y tests que ejerciten ambas ramas de la condición combinada.
