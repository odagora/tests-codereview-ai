# Overlay — Tour técnico de frontend

> Se usa **encima** de `TECHNICAL-TOUR-TEMPLATE.md`. No repite las 6 secciones;
> aporta el banco de preguntas y qué cuenta como evidencia en frontend.
> Responde solo lo que aplique al componente/módulo analizado.

## Qué cuenta como evidencia en frontend

| Sección | Evidencia típica |
|---|---|
| Entradas | props, params de router, stores/contexto, respuestas API, eventos de usuario |
| Salidas | JSX/render, callbacks, mutaciones de estado, navegación, analítica |
| Dependencias | componentes hijos, hooks, stores, design system, SDKs, utilidades |
| Flujo | mount/render → effects → acción de usuario → actualización de estado → re-render |

## 1. Responsabilidad

- [ ] ¿Es presentacional, contenedor, hook, store, ruta o utilidad?
- [ ] ¿Gestiona datos/estado o solo renderiza?
- [ ] ¿Es reutilizable o específico de una pantalla/feature?

## 2. Entradas

- [ ] ¿Qué props/params recibe y cuáles son obligatorios vs con default?
- [ ] ¿De dónde salen los datos: props, contexto, store, fetch, URL, estado local?
- [ ] ¿Hay eventos de usuario y qué los dispara?
- [ ] ¿Qué tipos y formas tienen los datos (nulos, parciales, loading/error)?

## 3. Salidas

- [ ] ¿Qué renderiza y qué consume ese render (padre, ruta, portal)?
- [ ] ¿Qué callbacks/eventos emite hacia el padre?
- [ ] ¿Qué efectos externos produce (navegación, fetch, storage, analytics)?

## 4. Dependencias

- [ ] ¿Qué componentes hijos/hooks/stores usa?
- [ ] ¿Depende del design system o de estilos propios?
- [ ] ¿Usa librerías de datos/estado (React Query, Redux, Zustand...)?

## 5. Flujo

- [ ] Traza: montaje → estado inicial → effects → interacción → actualización → re-render.
- [ ] ¿Qué dependencies tienen los effects y cuándo se re-ejecutan?
- [ ] ¿El estado es local, derivado o compartido?
- [ ] ¿Hay estados de carga/error/vacío y cómo se manejan?

## Riesgos a confirmar (no reportar aún)

- Ciclos de render y dependencias inestables en effects.
- Estado derivado duplicado o desincronizado.
- Fugas (suscripciones, timers, listeners sin cleanup).
- Condiciones de carrera en fetch/acciones del usuario.
- Accesibilidad, manejo de foco y estados vacíos.

## Punto de control (ejemplos)

1. ¿El límite de responsabilidad del componente está claro (qué NO hace)?
2. ¿Todos los orígenes de datos están identificados?
3. ¿Los efectos secundarios y sus disparadores están mapeados?
4. ¿Existen tipos/contratos de props y datos que fijen la forma esperada?
