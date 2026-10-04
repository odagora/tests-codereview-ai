# Plantilla — Tour técnico de un módulo

> Plantilla base, agnóstica al stack. Úsala junto con el overlay del dominio:
> `TECHNICAL-TOUR-BACKEND.md` o `TECHNICAL-TOUR-FRONTEND.md`.
> Objetivo: entender **qué hace** el código antes de auditar o modificar.
> En esta fase **no** se reportan bugs, vulnerabilidades ni recomendaciones.

## Cómo usar esta plantilla

1. Copia este archivo y renómbralo según el módulo: `tour-<modulo>.md`.
2. Completa el encabezado de contexto.
3. Llena las 6 secciones con el código/diff entregado.
4. Abre el overlay del dominio y responde solo las preguntas que apliquen.
5. Cierra con el punto de control.

## Reglas

- Analiza **solo** el archivo o diff proporcionado; no inventes contexto externo.
- Distingue siempre **Evidencia** (visible en el código, con cita `archivo:línea`)
  de **Inferencia** (deducción no confirmable).
- Cita funciones o líneas cuando estén disponibles.
- No reportes bugs, vulnerabilidades ni recomendaciones en esta fase.
- Si algo no se puede confirmar, va a supuestos, no a conclusiones.

---

## Contexto

- **Módulo / ruta:** `<ruta/al/archivo>`
- **Dominio:** `<backend | frontend | otro>`
- **Lenguaje / framework:** `<...>`
- **Alcance:** `<archivo completo | diff | función>`
- **Fecha del análisis:** `<...>`

---

## 1. Responsabilidad principal

**Evidencia:**
- `<qué hace el módulo y cuál es su punto de entrada, con cita>`

**Inferencia:**
- `<rol probable dentro del sistema; qué no es (p. ej. no es capa de persistencia)>`

## 2. Entradas y su origen

**Evidencia:** (parámetros, props, lectura de fuentes, eventos)
- `<entrada> — <origen visible en el código> (<cita>)`

**Inferencia:**
- `<origen real no visible; probable responsabilidad del llamador>`

## 3. Salidas y consumidores

**Evidencia:**
- `<valor/efecto retornado o producido, con cita>`

**Inferencia:**
- `<quién consume la salida, no visible en el código>`

## 4. Dependencias

**Internas (dentro del módulo):**
- `<símbolo/función usado y dónde, con cita>`

**Externas (librerías / paquetes):**
- `<import y para qué se usa, con cita>`

**Inferencia:**
- `<acoplamientos implícitos; si se usa inyección de dependencias, etc.>`

## 5. Flujo principal paso a paso

1. `<paso con cita>`
2. `<paso con cita>`
3. `<...>`

**Detalle de subfunciones relevantes:** `<breve desglose con citas>`

## 6. Supuestos / datos no confirmables

**Inferencia (no evidenciable):**
- `<supuesto sobre tipos, unidades, invariantes, orden, sincronía, etc.>`

---

## Overlay de dominio

Marca lo que aplique del overlay correspondiente:

- Backend → `TECHNICAL-TOUR-BACKEND.md`
- Frontend → `TECHNICAL-TOUR-FRONTEND.md`

Preguntas del overlay respondidas:

- [ ] `<pregunta>`
- [ ] `<pregunta>`

---

## Punto de control (a confirmar por un humano)

1. `<afirmación que un humano debe verificar antes de auditar>`
2. `<...>`
3. `<...>`
