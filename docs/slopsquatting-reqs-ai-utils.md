# Slopsquatting: requests-ai-utils

## Hallazgo

`requirements.txt:4` declara la dependencia `requests-ai-utils`. Según la salida de `python scripts/audit_dependencies.py requirements.txt`, esta dependencia tiene estado `not_found` en PyPI (normalizada como `requests-ai-utils`), a diferencia de `fastapi`, `uvicorn[standard]` y `semgrep`, que el mismo auditor reporta como `found` con versiones concretas. El propio script la lista bajo "Potential hallucinated dependencies".

## Evidencia

- Evidencia: `requirements.txt` contiene 4 líneas. Línea 4: `requests-ai-utils` (confirmado por lectura directa del archivo).
- Evidencia: `python scripts/audit_dependencies.py requirements.txt` devuelve, para la fila `requests-ai-utils`: `normalized=requests-ai-utils`, `status=not_found`, `latest=-`.
- Evidencia: el mismo comando reporta `fastapi` (`found`, `0.142.2`), `uvicorn[standard]`→`uvicorn` (`found`, `0.54.0`) y `semgrep` (`found`, `1.179.0`) como existentes en PyPI, lo que descarta un fallo general del auditor o de red: la consulta a PyPI funciona, y específicamente `requests-ai-utils` no resuelve.
- Evidencia: `grep` sobre el repositorio (código, Markdown, `requirements.txt`, `pyproject.toml`, excluyendo `.venv`) no encuentra ningún `import requests_ai_utils` ni otra referencia a `requests-ai-utils` fuera de la línea 4 de `requirements.txt`. No hay código en `src/` ni en `scripts/` que dependa de este paquete.
- Inferencia: dado que no hay ningún uso en el código y el nombre no aparece en ningún otro archivo del repositorio, la línea parece haber sido agregada sin que exista un consumidor real del paquete en el proyecto. No hay evidencia en el repositorio sobre cómo o por qué se agregó esa línea (no hay historial de commits ni autoría disponible en los insumos de esta revisión).
- No hay evidencia: el repositorio no contiene un archivo de lock (`requirements.lock`, `poetry.lock`, `uv.lock`, etc.) ni un archivo de política de dependencias. Esto se declara explícitamente porque esos insumos eran opcionales y no están presentes.

## Riesgo

El patrón observado es consistente con slopsquatting: una dependencia que no existe en el índice público (PyPI) pero que aparece en una lista de requisitos como si fuera real. Este patrón típico ocurre cuando una herramienta generativa (o un proceso que depende de una) "alucina" el nombre de un paquete plausible y lo escribe en `requirements.txt` sin verificar su existencia.

El vector de ataque asociado a slopsquatting es el siguiente: si un nombre alucinado se repite con suficiente frecuencia en código generado públicamente, un atacante puede registrar ese mismo nombre en PyPI y publicar un paquete malicioso bajo él. Cualquier instalación futura de `requirements.txt` (`pip install -r requirements.txt`) que ocurra después de ese registro instalaría ese paquete sin que nadie lo haya pedido deliberadamente, confiando en que "ya estaba en el archivo".

Impacto concreto para payments-svc:
- Hoy, `pip install -r requirements.txt` falla directamente porque el paquete no existe (no hay instalación silenciosa de código no verificado). Esto es evidencia, no inferencia: lo confirma el estado `not_found` del auditor.
- El riesgo no es que el paquete actual sea malicioso (no existe, por lo tanto no hay código que auditar), sino que la línea queda como una superficie de ataque latente: cualquiera (persona o proceso automatizado) con permisos de publicación en PyPI podría registrar `requests-ai-utils` en el futuro. Si en ese momento alguien reintenta instalar las dependencias sin volver a auditar, el servicio de pagos ejecutaría código de un tercero desconocido con control total sobre el entorno de ejecución (acceso a credenciales, red, y en este repositorio, a la capa de base de datos y lógica de refunds/pagos).
- Al no haber lockfile ni hashes, no existe ningún mecanismo en el repositorio que hubiera detectado o bloqueado esta línea antes de llegar a `requirements.txt`.

## Decisión

No instalar `requests-ai-utils`. No existe en PyPI, no tiene ningún uso en el código del repositorio, y no hay evidencia de que sea necesaria para el funcionamiento de payments-svc. La línea debe tratarse como no verificada hasta que alguien con contexto del proyecto confirme, con evidencia, para qué se agregó (y si la intención real era otro paquete, debe verificarse explícitamente cuál, en vez de asumir una corrección automática del nombre).

## Mitigaciones

- Eliminar la línea `requests-ai-utils` de `requirements.txt` en tanto no exista evidencia verificable de que corresponde a un paquete real y necesario.
- Incorporar `scripts/audit_dependencies.py` (ya presente en el repositorio) como un gate de CI que corra en cada cambio a `requirements.txt` y falle el build si aparece cualquier dependencia con `status != found`, en lugar de ejecutarlo solo manualmente.
- Adoptar un archivo de lock con hashes (por ejemplo `pip-compile --generate-hashes` o equivalente) para que las instalaciones futuras solo acepten versiones y artefactos verificados explícitamente, no lo que resuelva el índice en el momento de instalar.
- Requerir revisión humana explícita de cualquier línea nueva en `requirements.txt` antes de merge, en particular cuando la línea fue introducida o sugerida por una herramienta de generación de código, dado que este es exactamente el mecanismo que produce nombres de paquete alucinados.
- Revisar el historial de cambios de `requirements.txt` (control de versiones) para identificar cuándo y en qué contexto se agregó la línea; este repositorio no incluye ese historial como insumo de esta revisión, por lo que no se reporta aquí, pero es una acción recomendada con las herramientas de control de versiones ya disponibles en el proyecto.

## Relaciones con SBOM y NIST

Un SBOM (Software Bill of Materials) es un inventario explícito de todos los componentes de software que forman parte de un producto, incluyendo sus versiones y origen. Si este repositorio mantuviera un SBOM generado automáticamente a partir de `requirements.txt`, una entrada como `requests-ai-utils` habría quedado registrada como un componente declarado pero no resoluble, lo cual es precisamente el tipo de discrepancia que un proceso de verificación de SBOM (comparar el inventario declarado contra lo que realmente existe y se instala) está diseñado para detectar antes de que llegue a un entorno productivo.

Este repositorio no incluye un SBOM ni un archivo de políticas de dependencias entre los insumos disponibles para esta revisión, y no se encontró ninguno en el árbol del proyecto. Se declara explícitamente esta ausencia en lugar de asumir que existe un control equivalente.

En términos de gestión de componentes de software (alineado conceptualmente con las prácticas de gestión de riesgo de cadena de suministro descritas en el marco de ciberseguridad del NIST, en particular las referidas a Software Supply Chain Risk Management), el hallazgo de esta revisión ilustra la necesidad de que la verificación de existencia y procedencia de una dependencia ocurra antes de que el paquete pueda ser instalado, no después. Sin un SBOM, un lockfile con hashes o un gate automatizado, la única barrera actual contra esta clase de riesgo en payments-svc es la ejecución manual de `scripts/audit_dependencies.py`, que depende de que alguien decida correrlo.
