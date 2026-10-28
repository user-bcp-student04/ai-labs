---
name: pr-review-security
description: Revisión local de un PR centrada en seguridad: SQL parametrizado, autorización del lado servidor, secretos, carga de archivos, dependencias y supresiones de scanners. No publica comentarios ni aprueba el PR.
---

# PR Review: Seguridad

## Cuándo usar

Cuando un PR toca autenticación, endpoints, consultas a base de datos, carga de archivos, configuración de despliegue, dependencias o reglas de análisis estático.

Normalmente lo invoca [pr-review-orchestrator](../pr-review-orchestrator/SKILL.md), pero puede usarse solo.

## Criterio que se comprueba

Un PR cumple este aspecto si, en la versión revisada:

1. ninguna consulta SQL concatena entrada del usuario; se usan parámetros;
2. la autorización se decide en el servidor y ligada a la identidad autenticada;
3. no aparecen secretos reales ni credenciales en el código, configuración o pruebas;
4. la carga de archivos controla nombre, tamaño y extensión;
5. no se incorporan dependencias con vulnerabilidades High o Critical sin decisión documentada;
6. no se desactivan ni silencian CodeQL, Dependency Review, JaCoCo ni otros scanners (`# noqa`, `nosec`, exclusiones, supresiones).

No evalúa cobertura ni compatibilidad de contratos.

## Entradas

- número o URL del PR en `user-bcp-student04/ai-labs`;
- SHA de base y SHA de cabeza fijados al inicio.

## Procedimiento

1. **Fijar versión.** Con `github-official` (`pull_request_read`) obtén el PR, base y cabeza. Registra ambos SHA completos.
2. **Obtener el diff.** Pide diff y archivos en esos SHA. Prioriza `auth/`, `api/app/`, `web/src/`, `web/nginx.conf`, `Dockerfile`, `compose.yaml`, `pom.xml`, `requirements*.txt`, `pyproject.toml`, `package.json`, `uploads/` y `.github/`.
3. **Revisar SQL.** En líneas añadidas busca concatenación o interpolación en consultas: `f"...{`, `+` con variables en `execute`, `%` con cadenas, `.format(` sobre SQL. Confirma en la versión de cabeza que la consulta usa parámetros.
4. **Revisar autorización.** Confirma que cada endpoint nuevo o modificado valida autenticación y que el identificador de usuario viene del token o sesión, no de un parámetro controlado por el cliente.
5. **Revisar secretos.** Busca en líneas añadidas: `password=`, `secret=`, `token=`, claves con formato de credencial, cadenas largas en base64. Verifica si son valores de prueba aislados o variables de entorno.
6. **Revisar carga de archivos.** Si cambia `uploads/` o el manejo de archivos, confirma límites de tamaño, lista de extensiones y saneamiento de nombre (`..`, rutas absolutas).
7. **Revisar dependencias.** Lista dependencias añadidas o con versión cambiada en `requirements*.txt`, `pyproject.toml`, `package.json` o `pom.xml`. Marca como `RIESGO A CONFIRMAR` cualquier una que requiera revisión de vulnerabilidades; no inventes CVE.
8. **Revisar supresiones.** Busca en el diff: `# noqa`, `# nosec`, `@SuppressWarnings`, `eslint-disable`, `codeql` en workflows, exclusiones en `.github/`.
9. **Clasificar cada observación** (ver Salida).

## Reglas

- no publicar comentarios, reseñas ni aprobaciones en GitHub;
- no hacer merge ni modificar el PR;
- no ejecutar pruebas ofensivas ni escaneos contra sistemas externos;
- no reproducir un secreto completo en la revisión; redáctalo (por ejemplo `ABCD****`);
- no usar datos reales;
- no declarar una vulnerabilidad sin evidencia del diff o de una ejecución real.

## Clasificación

```text
DEFECTO DEMOSTRADO   - el diff muestra el patrón inseguro en la versión revisada; citar línea
RIESGO A CONFIRMAR   - indicio que requiere revisión humana o un scanner; indicar qué lo confirmaría
```

## Salida

```markdown
# Revisión local: seguridad

- PR: <enlace>
- Base: <SHA completo>
- Cabeza: <SHA completo>
- Criterio: SQL parametrizado, autorización servidor, secretos, carga de archivos, dependencias y supresiones

## Observaciones
### <título>
- Clasificación: DEFECTO DEMOSTRADO | RIESGO A CONFIRMAR
- Ubicación: <archivo>:<línea o fragmento del diff>
- Evidencia: <fragmento literal, con secretos redactados>
- Comprobación que lo confirmaría: <p. ej. revisar CodeQL, prueba con entrada maliciosa en laboratorio>

## Comprobaciones realizadas
- <comprobación>: <resultado> (incluso si no hubo observaciones)

## Limitaciones
- <qué no se revisó, p. ej. no se consultó base de vulnerabilidades externa>

Esta revisión es local y no constituye aprobación del PR.
```
