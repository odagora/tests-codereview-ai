# Reporte de acuerdo IA-vs-humano

Este reporte compara etiquetas humanas contra etiquetas normalizadas del revisor ruteado.
La unidad de comparacion es binaria: para cada caso y categoria, el hallazgo esta presente o no.

El dataset es pequeno y sirve para calibracion de demo, no como benchmark productivo.

## Resumen por categoria

| Categoria | Casos | Acuerdo | Kappa | TP | TN | FP | FN | Politica sugerida |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| correctness | 5 | 80% | 0.62 | 2 | 2 | 1 | 0 | `warn` |
| documentation | 5 | 80% | 0.55 | 1 | 3 | 0 | 1 | `warn` |
| security | 5 | 100% | 1.00 | 2 | 3 | 0 | 0 | `block` |
| tests | 5 | 60% | 0.29 | 1 | 2 | 0 | 2 | `human_required` |

## Politica

- `block`: puede bloquear cuando el hallazgo sea `blocker` y la categoria tenga acuerdo alto.
- `warn`: comenta el hallazgo, pero no bloquea automaticamente.
- `human_required`: requiere decision humana antes de bloquear.

## Lectura

El revisor no tiene la misma confiabilidad en todas las categorias.
Las categorias con menor kappa deben usarse como senal de revision, no como gate automatico.
