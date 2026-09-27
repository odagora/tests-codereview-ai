# Revisor ruteado de PRs — payments-svc

## Contexto
Revisa los cambios de la rama actual contra `develop`.
Trata este diff como si fuera un Pull Request hacia `develop`, aunque no exista un PR real en GitHub.
No mezcles archivos de tipos distintos en el mismo bloque.
No cambies el contenido del diff.
Usa solo el diff mostrado y los archivos incluidos.
No inventes información de GitHub, CI o historial remoto.

## Ruteo
Separa mentalmente los archivos del diff por tipo y aplica el foco correspondiente:
- Python (`.py`): SQL, autorización y comportamiento async. Usar `prompts/reviewer-python.md`
- TypeScript (`.ts`, `.tsx`): tipos, manejo de errores, idempotencia y fugas al cliente. Usar `prompts/reviewer-typescript.md`
- Infraestructura (`.yml`, `.yaml`, `.github/`): secretos y permisos del workflow. Usar `prompts/reviewer-infra.md`

Ignora criterios que no correspondan al tipo de archivo.
Si varios archivos exponen el mismo riesgo, conserva un solo hallazgo, anclado a la ubicación más útil.

## Priorización
- Reporta solo hallazgos accionables relacionados con el cambio.
- Ordena por severidad: `blocker`, `advisory`, `info`.
- Limita la salida a los hallazgos más importantes del PR.
- No agregues observaciones de estilo si desplazan un riesgo de corrección o seguridad.

## Salida
Genera un archivo JSON en `samples/reviews/` con nombre descriptivo en kebab-case terminando en `.json`.
Ejemplo: `manual-refund-review.json`.

El contenido del archivo debe cumplir el mismo contrato: una lista JSON de hallazgos:

```json
{
	"rule_id": "SEC-AUTHZ-001",
	"category": "security",
	"severity": "blocker",
	"location": {
		"file": "src/payments_svc/api.py",
		"line": 96
	},
	"message": "Endpoint sin verificación de autorización",
	"suggested_fix": "Validar permisos antes de procesar el refund"
}
```

No separes el JSON por archivo. Si no hay hallazgos, devuelve `[]`.