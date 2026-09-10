Revisa el diff de la rama actual contra `develop` como si fuera un PR.
Usa solo los archivos mostrados. No inventes contexto de GitHub, CI o historial remoto.

**Reglas:**
- No reescribas código ni propongas refactors grandes.
- Solo reporta hallazgos accionables y relacionados con el cambio.

## Rúbrica

| # | Categoría | Severidad |
|---|-----------|-----------|
| 1 | **Corrección** — El código cumple el contrato del dominio de pagos | Alta |
| 2 | **Seguridad** — Autorización, autenticación, exposición de datos o entradas inseguras | Alta |
| 3 | **Rendimiento** — Complejidad innecesaria o trabajo costoso en rutas calientes | Media |
| 4 | **Tests faltantes** — Cambios sin pruebas relevantes o sin casos de borde | Media |
| 5 | **Estilo** — Legibilidad, nombres y mantenibilidad | Baja |
| 6 | **Documentación** — Cambios públicos sin documentación suficiente | Baja |

## Formato de salida

Para cada categoría:
1. Indica si hay hallazgos (sí/no)
2. Si hay: cita archivo y línea exacta
3. Explica por qué importa
4. Sugiere una corrección breve

Si una categoría no tiene hallazgos, escribe "sin hallazgos".
No inventes archivos ni líneas.
