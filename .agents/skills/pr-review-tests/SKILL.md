---
name: pr-review-tests
description: Revisión local de un PR centrada en pruebas: cobertura de los cambios de comportamiento, pruebas desactivadas o debilitadas y umbrales de calidad. No publica comentarios ni aprueba el PR.
---

# PR Review: Pruebas

## Cuándo usar

Cuando un PR cambia código o pruebas y se necesita verificar que el comportamiento modificado está protegido por pruebas que realmente se ejecutan.

Normalmente lo invoca [pr-review-orchestrator](../pr-review-orchestrator/SKILL.md), pero puede usarse solo.

## Criterio que se comprueba

Un PR cumple este aspecto si, en la versión revisada:

1. cada cambio de comportamiento del diff tiene una prueba nueva o existente que lo ejercita;
2. ninguna prueba queda desactivada, vacía o debilitada sin justificación;
3. los umbrales de cobertura y los gates de calidad no se han reducido;
4. debe utilizar correctamente el patrón AAA (Arrange, Act, Assert) en las pruebas unitarias
5. Todo unitTest utiliza CamelCase.
6. el código modificado alcanza la meta de cobertura del 85 % cuando exista reporte.

No evalúa seguridad ni compatibilidad de contratos; para eso están los otros revisores.

## Entradas

- número o URL del PR en el repositorio `user-bcp-student04/ai-labs`;
- SHA de base y SHA de cabeza fijados al inicio (ver Procedimiento, paso 1).

## Procedimiento

1. **Fijar versión.** Con `github-official` (`pull_request_read`) obtén el PR, su base y su cabeza. Registra ambos SHA completos. Si el PR cambia durante la revisión, detén la revisión y repítela.
2. **Obtener el diff.** Pide el diff y la lista de archivos del PR en esos SHA. Separa archivos de código, archivos de prueba y configuración de pruebas o cobertura.
3. **Mapear cambios de comportamiento.** Para cada función, endpoint o componente modificado en el diff, anota la línea o fragmento donde cambia.
4. **Buscar prueba asociada.** Localiza la prueba que cubre ese cambio en la misma versión (`get_file_contents` con el SHA de cabeza). Referencias del repositorio:
   - API: `api/tests/test_api.py`;
   - Auth: `auth/src/test/java/`;
   - Web: archivos `*.spec.ts` bajo `web/src/`.
5. **Buscar debilitamientos en el diff.** Revisa líneas añadidas o eliminadas que contengan:
   - desactivación: `@Disabled`, `@Ignore`, `it.skip`, `xit`, `describe.skip`, `pytest.mark.skip`, `pytest.mark.xfail`;
   - aserciones eliminadas o sustituidas por `assert True`;
   - pruebas borradas sin reemplazo;
   - cambios en umbrales de `pom.xml` (JaCoCo), `vitest.config.ts` o configuración de cobertura de `api`.
6. **Ejecutar solo si corresponde.** Si decides ejecutar pruebas, hazlo sobre el SHA de cabeza (worktree temporal o checkout del SHA) con `python tools/lab.py test api|auth|web` desde la raíz. Registra el comando exacto y su resultado real. Si no ejecutas, marca la comprobación como `NO EJECUTADO`.
7. **Clasificar cada observación** (ver Salida).

## Reglas

- no publicar comentarios, reseñas ni aprobaciones en GitHub;
- no hacer merge ni modificar el PR;
- no afirmar que una prueba pasó sin haberla ejecutado en esta revisión;
- no desactivar ni editar pruebas para que pasen;
- citar siempre archivo y línea o fragmento del diff revisado;
- no usar datos reales ni secretos al ejecutar pruebas.

## Clasificación

```text
DEFECTO DEMOSTRADO   - el diff o una ejecución real muestra el problema; citar evidencia y comando si lo hubo
RIESGO A CONFIRMAR   - hay indicio en el diff pero falta ejecutar o revisar algo; indicar qué prueba lo confirmaría
```

## Salida

```markdown
# Revisión local: pruebas

- PR: <enlace>
- Base: <SHA completo>
- Cabeza: <SHA completo>
- Criterio: pruebas que cubren cambios, sin desactivaciones ni umbrales reducidos

## Observaciones
### <título>
- Clasificación: DEFECTO DEMOSTRADO | RIESGO A CONFIRMAR
- Ubicación: <archivo>:<línea o fragmento del diff>
- Evidencia: <fragmento literal>
- Prueba o comprobación que lo confirmaría: <descripción o comando>

## Comprobaciones realizadas
- <comprobación>: <resultado> (incluso si no hubo observaciones)

## Ejecución de pruebas
- <comando exacto>: <resultado real> | NO EJECUTADO

## Limitaciones
- <qué no se revisó>

Esta revisión es local y no constituye aprobación del PR.
```
