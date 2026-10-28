---
name: pr-review-compatibility
description: Revisión local de un PR centrada en compatibilidad: contratos de endpoints, formatos consumidos por el frontend, esquema de datos y configuración. No publica comentarios ni aprueba el PR.
---

# PR Review: Compatibilidad

## Cuándo usar

Cuando un PR cambia endpoints, modelos de respuesta, validaciones de entrada, esquema de base de datos, configuración o código consumido por otro componente.

Normalmente lo invoca [pr-review-orchestrator](../pr-review-orchestrator/SKILL.md), pero puede usarse solo.

## Criterio que se comprueba

Un PR cumple este aspecto si, en la versión revisada:

1. los contratos protegidos conservan ruta, método, campos de entrada, campos de salida y códigos HTTP:
   - `POST /auth/login`
   - `GET /api/tasks`, `POST /api/tasks`
   - `GET /api/summary`
   - `POST /api/requirements`
2. el frontend (`web/src/`) sigue pudiendo consumir las respuestas sin cambios no anunciados;
3. el esquema de datos (`auth/data/workshop.db`, migraciones o SQL) no elimina ni renombra columnas usadas sin plan de migración;
4. la configuración (`application.properties`, `compose.yaml`, variables de entorno, puertos) mantiene nombres y valores por defecto compatibles.

No evalúa seguridad ni cobertura.

## Entradas

- número o URL del PR en `user-bcp-student04/ai-labs`;
- SHA de base y SHA de cabeza fijados al inicio.

## Procedimiento

1. **Fijar versión.** Con `github-official` (`pull_request_read`) obtén el PR, base y cabeza. Registra ambos SHA completos.
2. **Obtener el diff.** Pide diff y archivos en esos SHA.
3. **Construir la línea base del contrato.** Lee en el SHA de **base** los archivos de rutas y modelos afectados (`get_file_contents` con ese SHA) para fijar el contrato original. Sustenta cada contrato con la línea del archivo en base.
4. **Comparar con la cabeza.** En el diff, busca cambios en: rutas, nombres de campos, tipos, obligatoriedad, códigos de respuesta, formato de fechas y mensajes de error usados por el frontend.
5. **Cruzar con consumidores.** Busca en `web/src/` (SHA de cabeza) el uso de cada campo o ruta modificada. Un campo eliminado o renombrado usado por el frontend es un hallazgo.
6. **Revisar datos y configuración.** Si cambian modelos de base de datos, consultas de creación de tablas o `application.properties`, `compose.yaml` o Dockerfiles, compara con la versión de base.
7. **Clasificar cada observación** (ver Salida).

## Reglas

- no publicar comentarios, reseñas ni aprobaciones en GitHub;
- no hacer merge ni modificar el PR;
- el contrato de referencia es el del SHA de base, no la memoria ni suposiciones;
- no declarar incompatibilidad sin citar el campo o ruta en ambas versiones cuando aplique;
- un cambio no anunciado en un contrato protegido es `DEFECTO DEMOSTRADO` solo si el diff lo muestra; si depende de un consumidor externo no visible, es `RIESGO A CONFIRMAR`;
- no ejecutar cambios de esquema sobre `workshop.db` real; si hace falta comprobarlo, usa una copia temporal en el laboratorio.

## Clasificación

```text
DEFECTO DEMOSTRADO   - el diff cambia un contrato protegido o un consumidor visible sin adaptación
RIESGO A CONFIRMAR   - el cambio puede afectar a un consumidor o dato no visible en el diff
```

## Salida

```markdown
# Revisión local: compatibilidad

- PR: <enlace>
- Base: <SHA completo>
- Cabeza: <SHA completo>
- Criterio: contratos protegidos, consumidores del frontend, esquema y configuración

## Contratos revisados
| Contrato | En base | En cabeza | Estado |
|---|---|---|---|
| <ruta o campo> | <archivo:línea> | <archivo:línea> | sin cambio / cambiado / no aplica |

## Observaciones
### <título>
- Clasificación: DEFECTO DEMOSTRADO | RIESGO A CONFIRMAR
- Ubicación: <archivo>:<línea o fragmento del diff>
- Evidencia: <fragmento en base y en cabeza>
- Prueba o comprobación que lo confirmaría: <p. ej. prueba de contrato en api/tests/test_api.py>

## Comprobaciones realizadas
- <comprobación>: <resultado> (incluso si no hubo observaciones)

## Limitaciones
- <qué no se revisó, p. ej. consumidores fuera de web/src>

Esta revisión es local y no constituye aprobación del PR.
```
