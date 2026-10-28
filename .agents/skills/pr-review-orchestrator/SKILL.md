---
name: pr-review-orchestrator
description: Orquestador de revisiones locales de PR que fija SHA base y cabeza, ejecuta solo los aspectos (pruebas, seguridad, compatibilidad) indicados en la petición y consolida un único informe. No publica comentarios ni aprueba el PR.
---

# PR Review: Orquestador

## Cuándo usar

Cuando se pida revisar un PR del repositorio `user-bcp-student04/ai-labs` y la petición indique explícitamente uno, dos o los tres aspectos a revisar.

## Entradas

| Entrada | Obligatoria | Valores |
|---|---|---|
| PR | sí | número del PR (por ejemplo `#24`) del repositorio `user-bcp-student04/ai-labs` |
| repositorio | no | `owner/repo`; por defecto `user-bcp-student04/ai-labs` |
| `aspectos` | sí | uno o más de: `pruebas`, `seguridad`, `compatibilidad` |

Reglas de la entrada:

- `aspectos` debe venir explícito en la petición. No lo deduzcas del diff ni asumas los tres por defecto.
- Si falta `aspectos` o contiene un valor fuera de la lista, detente y pregunta con `ask_user`. No inicies la revisión.
- Solo se ejecutan los aspectos indicados. Un aspecto no pedido no se revisa, aunque el diff lo toque; en ese caso anótalo en Limitaciones como "no solicitado".

## Revisores

| Valor de `aspectos` | Skill | Aspecto |
|---|---|---|
| `pruebas` | [pr-review-tests](../pr-review-tests/SKILL.md) | Pruebas |
| `seguridad` | [pr-review-security](../pr-review-security/SKILL.md) | Seguridad |
| `compatibilidad` | [pr-review-compatibility](../pr-review-compatibility/SKILL.md) | Compatibilidad |

## Procedimiento

1. **Validar entrada.** Confirma PR y `aspectos`. Si falta algo, aplica la regla de `ask_user` de arriba.
2. **Buscar el PR.** Con el MCP `github-official` (herramienta `pull_request_read`), busca el PR por número en el repositorio de la entrada. Confirma que existe y registra su estado. Si no se encuentra, detente e informa `BLOQUEADO` con la causa; no revises otro PR.
3. **Fijar versión.** Del mismo PR, obtén base y cabeza. Registra SHA completos. Todos los revisores usarán estos mismos SHA.
4. **Redirigir el trabajo.** Invoca únicamente el skill de cada aspecto indicado, uno por uno o en paralelo si el entorno lo permite. A cada uno pasa el número de PR y los mismos SHA base y cabeza.
5. **Verificar consistencia.** Confirma que todos los revisores usaron los mismos SHA. Si el PR cambió durante la revisión o los SHA difieren, descarta los resultados y repite desde el paso 3.
6. **Consolidar.** Une las observaciones de los aspectos solicitados en un único informe. Si dos revisores señalan la misma línea, agrúpalas y conserva la clasificación más conservadora (`RIESGO A CONFIRMAR` si una de las evidencias no es concluyente).
7. **Entregar.** Presenta el informe local. No publiques comentarios ni reseñas.

## Reglas

- no publicar comentarios, reseñas ni aprobaciones en GitHub;
- no hacer merge, cerrar ni modificar el PR;
- no ejecutar revisores de aspectos no solicitados;
- no presentar la ausencia de observaciones como aprobación;
- no afirmar que una prueba pasó sin ejecución registrada;
- si un revisor solicitado no pudo completar su procedimiento, informa `BLOQUEADO` con la causa.

## Salida

```markdown
# Revisión local del PR

- PR: <enlace>
- Base: <SHA completo>
- Cabeza: <SHA completo>

## Aspectos solicitados
| Aspecto | Estado | Motivo |
|---|---|---|
| Pruebas | SOLICITADO-COMPLETADO / SOLICITADO-BLOQUEADO / NO SOLICITADO | <causa o archivos revisados> |
| Seguridad | SOLICITADO-COMPLETADO / SOLICITADO-BLOQUEADO / NO SOLICITADO | <causa o archivos revisados> |
| Compatibilidad | SOLICITADO-COMPLETADO / SOLICITADO-BLOQUEADO / NO SOLICITADO | <causa o archivos revisados> |

## Observaciones consolidadas
| # | Aspecto | Clasificación | Ubicación | Resumen |
|---|---|---|---|---|
| 1 | <aspecto> | DEFECTO DEMOSTRADO / RIESGO A CONFIRMAR | <archivo:línea> | <resumen> |

Detalle de cada observación: ver el informe del revisor correspondiente.

## Comprobaciones realizadas
- <resumen por revisor>

## Limitaciones
- <qué no se pudo revisar o ejecutar>

Esta revisión es local y no constituye aprobación del PR.
```
