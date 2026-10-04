# Triaje de seguridad — payments-svc

Clasificación de los hallazgos de Semgrep en `samples/semgrep/semgrep-results.json`.

Evidencia usada: únicamente la salida de Semgrep y los archivos citados por ella
(`src/payments_svc/db.py` y `src/payments_svc/ops.py`), con las líneas señaladas abiertas
antes de clasificar.

| archivo | líneas | reglas | clasificación | justificación | siguientes pasos |
| --- | --- | --- | --- | --- | --- |
| src/payments_svc/db.py | 21-23 | python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query | true | El parámetro `email` se concatena directamente en la sentencia SQL: `"...WHERE email = '" + email + "'"` (línea 21) y la cadena resultante se ejecuta en `connection.execute(query)` (línea 23). No hay validación ni parametrización previa de `email`, por lo que el patrón de inyección SQL es real (el código usa `sqlite3`, no SQLAlchemy, pero la clase de vulnerabilidad CWE-89 es la misma). | Parametrizar con placeholder: `connection.execute("... WHERE email = ?", (email,))`, como ya se hace en la línea 34. Verificar de dónde proviene `email` para confirmar el origen no confiable. |
| src/payments_svc/db.py | 47-52 | python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query | false positive | Aunque la línea 51 concatena `status` en la query y la 52 la ejecuta, antes hay una lista blanca que restringe el valor: `allowed_statuses = {"active", "blocked", "pending"}` e `if status not in allowed_statuses: raise ValueError(...)` (líneas 47-49). El valor concatenado solo puede ser uno de esos tres literales, por lo que no es inyectable. | Sin acción obligatoria. Opcionalmente parametrizar por consistencia con la línea 34. |
| src/payments_svc/ops.py | 7-13 | python.lang.security.audit.subprocess-shell-true.subprocess-shell-true | false positive | `shell=True` está presente (línea 13), pero `job_name` se valida contra la lista blanca `allowed_jobs = {"daily-settlement", "refund-audit"}` antes de concatenarse (líneas 7-9). El comando concatenado solo puede contener esos literales, por lo que no hay inyección de comandos. | Sin acción obligatoria. Se puede mantener `shell=False` con lista de argumentos como endurecimiento, pero no es explotable con el código actual. |
| src/payments_svc/ops.py | 18-22 | python.lang.security.audit.subprocess-shell-true.subprocess-shell-true | true | `run_support_diagnostic(command)` recibe un string arbitrario y lo ejecuta directamente con `subprocess.run(command, shell=True, ...)` (líneas 19-21), sin ninguna validación, lista blanca ni separación de argumentos. Es un sink de OS Command Injection (CWE-78) sin protección. | Reemplazar por `subprocess.run([...], shell=False)` con argumentos explícitos y una lista blanca de comandos/subcomandos permitidos. Confirmar la procedencia de `command` (p. ej. quién invoca `run_support_diagnostic`) para acotar la explotabilidad real. |

## Notas de alcance

- Las cuatro coincidencias pertenecen a dos archivos, ambos citados por Semgrep; no se revisaron
  otros archivos porque la evidencia permitida se limita a los citados.
- Las líneas citadas (21, 23, 47-49, 51-52, 7-9, 13, 18-21) son líneas reales de los archivos leídos.
- En las dos clasificaciones `true`, la confirmación del origen no confiable del parámetro requiere
  revisar a los llamadores; si no puede establecerse con el código disponible, el punto a verificar
  es la procedencia de `email` y `command`.
