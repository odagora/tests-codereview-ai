# Overlay — Tour técnico de backend

> Se usa **encima** de `TECHNICAL-TOUR-TEMPLATE.md`. No repite las 6 secciones;
> aporta el banco de preguntas y qué cuenta como evidencia en backend.
> Responde solo lo que aplique al módulo analizado.

## Qué cuenta como evidencia en backend

| Sección | Evidencia típica |
|---|---|
| Entradas | firma de función/endpoint, mensajes de cola, consultas a DB, args de CLI, payloads, cron |
| Salidas | response, eventos emitidos, escrituras en DB, logs, código de retorno |
| Dependencias | repositorios, servicios, clients HTTP, ORM, cache, config |
| Flujo | request → handler → dominio → persistencia → respuesta/evento |

## 1. Responsabilidad

- [ ] ¿Es un endpoint, un caso de uso, un servicio de dominio, un worker o un job?
- [ ] ¿Es orquestación o lógica de negocio pura?
- [ ] ¿Respeta la separación de capas del proyecto (handler ≠ dominio ≠ persistencia)?

## 2. Entradas

- [ ] ¿De dónde vienen los datos: HTTP, DB, cola, archivo, otro servicio, cron?
- [ ] ¿Se validan en el borde o confían en el llamador?
- [ ] ¿Hay parámetros con defaults que cambian el comportamiento (moneda, flags, entorno)?
- [ ] ¿Qué formato/tipo tienen (paginación, IDs, fechas, decimales)?

## 3. Salidas

- [ ] ¿Qué contrato expone (response, evento, filas, efectos secundarios)?
- [ ] ¿Quién consume la salida (otro servicio, cliente, tabla, cola)? ¿Es visible?
- [ ] ¿La operación es de lectura o produce mutaciones?

## 4. Dependencias

- [ ] ¿Depende de servicios externos, y cómo se inyectan (interfaces/Protocols)?
- [ ] ¿Usa transacciones, connection pool, o sesiones de DB?
- [ ] ¿Tiene cache, rate limiting, reintentos o timeouts?

## 5. Flujo

- [ ] Traza el camino: entrada → validación → dominio → persistencia/IO → salida.
- [ ] ¿Hay puntos de idempotencia (reintentos, reprocesos)?
- [ ] ¿Hay efectos secundarios ocultos (emails, eventos, métricas, escrituras)?

## Riesgos a confirmar (no reportar aún)

- Consistencia transaccional y límites de transacción.
- Idempotencia y reprocesamiento.
- Concurrencia, locks, carreras.
- Manejo de errores y estados parciales.
- Coste de IO (N+1, llamadas síncronas encadenadas).

## Punto de control (ejemplos)

1. ¿El rol real del módulo coincide con la capa donde vive?
2. ¿Los orígenes de datos están confirmados con el llamador/config?
3. ¿Los efectos secundarios están todos identificados?
4. ¿Existen contratos (schemas, interfaces) que fijen tipos y unidades?
