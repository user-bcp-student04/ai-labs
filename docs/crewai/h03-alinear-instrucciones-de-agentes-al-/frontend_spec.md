# frontend_spec.md

## 1. Resumen

**Sin cambios en el frontend.**

El Issue [H03] «Alinear instrucciones de agentes al alcance web-only» cambia el texto de las instrucciones de los agentes. No cambia el producto. Por eso no se entregan componentes, servicios, rutas, plantillas ni estilos Angular, y este documento no incluye ningún bloque de código.

## 2. Justificación según el Issue y el plan de Arquitectura

- **Objetivo del Issue:** alinear las instrucciones de los agentes al contrato W2 y a la demo Angular web-only, «sin alterar los contratos ni el orden del pipeline». El resultado esperado es texto de instrucciones, no una pantalla nueva.
- **Tarea 2.3 (Frontend):** pide *exigir* en las instrucciones Angular 17 standalone, servicios tipados, `environment.ts`, estados, accesibilidad e idempotencia, y preservar la extracción/publicación `frontend-angular/` → `web/`. Es una exigencia sobre lo que un agente debe producir en futuras entregas, y no pide implementar un recorrido de usuario ahora.
- **Fuera del alcance (user_story.md, 1.3):** el plan de Arquitectura excluye explícitamente «Cambios en el código de la demo Angular. Solo se ajustan las instrucciones que guían a los agentes». También excluye cambios en el backend, en los contratos fuente (`bcp-wallet-mock-openapi.yaml`, `detalle H3.txt`), autenticación, QR y `tools/lab.py` o `ng test`.
- **Criterio 3 del Issue:** «No cambian identificadores, extracción, publicación ni orden del pipeline». Generar archivos bajo `frontend-angular/` modificaría lo que se publica en `web/` y contradiría este criterio.
- **Sin recorrido de usuario nuevo:** el Issue no define campos, validaciones, acciones, mensajes ni estados de pantalla. El contrato W2 no está disponible en el contexto (pendiente P2), así que inventar endpoints o campos violaría la regla de no inventar contrato.
- **Coherencia con el backend:** `backend_spec.md` declara «Sin cambios en backend» y no hay endpoints propios.

## 3. Entregables de este rol

| Entregable | Estado |
|---|---|
| Componentes, servicios, `app.routes.ts` y `app.component.ts` | No se entregan (sin cambios en el frontend) |
| `main.ts`, `index.html`, `package.json`, `angular.json` | No se tocan |
| Archivos bajo `frontend-angular/` y `web/` | Sin modificaciones |

Campos, validaciones, acciones, mensajes, estados de carga/vacío/éxito/error y accesibilidad: **no aplican**. No hay pantalla nueva ni modificada. La demo Angular existente conserva su comportamiento actual.

## 4. Cómo comprobar que el frontend no cambió

Ninguna de estas comprobaciones se ha ejecutado (**NO EJECUTADO**). Quien las ejecute debe conservar la salida real.

**Caso válido: no hay cambios en el frontend**
- Comandos: `git diff --stat -- frontend-angular/ web/` y `git diff --name-only -- frontend-angular web`
- Resultado esperado: salida vacía en ambos.

**Caso de error: se detectan cambios no permitidos**
- Comando: `git diff --name-only -- frontend-angular web | grep . && echo "VIOLACION: hay cambios en el frontend"`
- Resultado esperado si el cambio es correcto: sin salida. Si imprime archivos y la frase «VIOLACION», se incumplió el alcance y debe revertirse o escalarse.

**Preservación de identificadores, extracción y publicación (criterio 3)**
- Comando: `git diff -U0` sobre los archivos de los agentes.
- Resultado esperado: sin líneas modificadas en `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, la firma de `build_task(feature)` ni el orden del pipeline.

**Contenido de las instrucciones del agente de Frontend (tarea 2.3)**
- Comandos: `git grep -n "Angular 17"`, `git grep -n "environment.ts"` y `git grep -n "frontend-angular/"`.
- Resultado esperado: coincidencias en el texto de las instrucciones actualizadas. Las instrucciones deben mencionar Angular 17 standalone, servicios tipados, `environment.ts`, estados, accesibilidad e idempotencia, y mantener la extracción `frontend-angular/` → `web/`.

**Verificación del repositorio (tarea 2.6)**
- Comandos: `python -m pytest` (supuesto pendiente de confirmar, P3) y `python tools/verify.py`, seguido de `echo $?`.
- Resultado esperado: sin fallos y código de salida 0. Si hay fallos, se documentan con la salida real.

**No se usan:** `ng test`, `ng build`, `ng serve` ni `python tools/lab.py`. Como no hay código nuevo, no son necesarios, y 2.4 prohíbe `tools/lab.py` y `ng test`.

## 5. Supuestos y pendientes

**Supuestos**
- **F1.** El Issue y el plan de Arquitectura mandan sobre el prompt genérico del rol, que pide componentes y servicios. Entregar código fuera del alcance del Issue sería incumplir el alcance.
- **F2.** La demo Angular web-only existente no requiere cambios. Si un Issue posterior pide un recorrido de usuario, se implementará entonces con Angular 17 standalone contra el contrato W2 aprobado.
- **F3.** No hay identidad ni autenticación (2.5) ni persistencia en el cliente.

**Pendientes (heredados del plan de Arquitectura)**
- **P1.** Ruta de los archivos que definen `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent` y `build_task(feature)`.
- **P2.** Contenido de `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt`. Es imprescindible para cualquier recorrido futuro que consuma W2.
- **P3.** Comando exacto de las pruebas de contratos.
- **P4.** Alcance real de `python tools/verify.py`.
- **P5.** Comandos disponibles para cubrir navegador/mock (2.4).
- **P6.** Contenido de los «criterios H03 adaptados» (2.5).
- **P7.** Aceptar la brecha: no hay prueba automática del contenido textual de las instrucciones, que se verifica por revisión del diff y `git grep`.