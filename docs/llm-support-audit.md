# Auditoría LLM — `src/payments_svc/llm_support.py`

Línea base: `PYTHONPATH=src python3 scripts/check_llm_support.py` → `exposed risks: 3/3`
(ejecutado localmente; usa `FakeSupportLLM`, sin proveedor externo).

Etiquetas: **[V]** verificado en código o por ejecución local · **[I]** inferencia.

## Mitigaciones

### M1. Atar la herramienta a la cuenta autenticada (least agency)
- **Riesgo que reduce:** LLM06 Excessive agency / acceso cruzado entre cuentas.
  `get_refund_history(account_id)` (línea 71) acepta cualquier id y
  `answer_refund_question` la expone tal cual (línea 84). **[V]**
- **Control:** construir la tool como closure con la cuenta de sesión, sin
  parámetro controlable por el modelo, p. ej.
  `tools={"refund_history": lambda _ignored=None: get_refund_history(account_id)}`;
  además validar en `get_refund_history` que el solicitante == dueño.
  El fix debe vivir en la capa de tools: `FakeSupportLLM.complete` (línea 54)
  llama con el literal `"acct_vip_002"`, así que cualquier filtro basado en el
  prompt no lo detiene. **[V]**
- **Verificación:** `check_llm_support.py`, check `confused-deputy-cross-account`
  y las variantes P4 y P6 del reporte.
- **Antes / después:** antes la respuesta contiene `rf_9001` (`[RISK]`);
  después no debe aparecer `rf_9001` ni `999.00` para `acct_100`
  (`[OK]`), o debe devolver un error de autorización.

### M2. No tratar el system prompt como dato recuperable
- **Riesgo que reduce:** LLM07 System prompt leakage.
  La rama de las líneas 50–51 devuelve `SYSTEM_PROMPT` ante
  `"system prompt"` / `"ignore previous instructions"`. **[V]**
- **Control:** (a) guardia de salida que bloquee cualquier respuesta que
  contenga `SYSTEM_PROMPT` o un canary; (b) no poner nada sensible en el prompt
  (hoy solo hay política, no secretos **[V]**); (c) eliminar esa rama del fake
  para que represente un modelo que sí cumple la política.
- **Verificación:** checks `direct-system-prompt-leak` e `indirect-injection-note`.
- **Antes / después:** desaparece `SYSTEM PROMPT:` de `result.answer`.

### M3. Separar instrucciones de contenido no confiable
- **Riesgo que reduce:** LLM01 Prompt injection directa e indirecta.
  `build_support_prompt` (línea 66) interpola `user_question` crudo en el mismo
  bloque que las instrucciones. **[V]**
- **Control:** mensajes con roles separados (system / user), contenido de
  notas o terceros delimitado y marcado como dato, y normalizar o rechazar
  líneas que imiten el marcador `Current account:` (`_extract_account_id`,
  línea 89). **[I]** Esto reduce, no elimina, la inyección en un modelo real;
  por eso M1 y M2 son los controles que dan garantía.
- **Verificación:** test unitario sobre `build_support_prompt` que compruebe que
  el texto del usuario no aparece fuera del bloque delimitado. El fake usa
  coincidencia de palabras clave e ignora delimitadores, así que el script
  no puede demostrar esta mitigación. **[V]**
- **Antes / después:** el prompt deja de tener el input en el nivel de instrucción.

### M4. Hacer que el script falle cuando hay riesgo (gate de CI)
- **Riesgo que reduce:** regresiones silenciosas. `main` devuelve siempre `0`
  (línea 61 del script), aunque haya `3/3` expuestos. **[V]**
- **Control:** `return 1 if exposed_count else 0`, y tests `pytest` que aserten
  la ausencia de `SYSTEM PROMPT:` y `rf_9001`.
- **Antes / después:** antes salida `0` con `3/3`; después salida `0` solo con `0/3`.

### Orden recomendado
M1 → M2 → M4 → M3.
