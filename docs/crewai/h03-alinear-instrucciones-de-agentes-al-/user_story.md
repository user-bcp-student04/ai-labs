# user_story.md

## Historia de usuario

**Como** responsable del laboratorio de agentes (pipeline de entrega del cambio `proximity-contact-payment`),
**quiero** que las instrucciones de cada agente (Arquitectura, Backend, Frontend, Pruebas, Seguridad/Chapter) describan el alcance web-only del contrato W2 y de la demo Angular,
**para** que los agentes produzcan entregables coherentes con ese alcance, sin alterar los contratos, la extracción/publicación ni el orden del pipeline.

**Nota sobre el tipo de cambio:** es un cambio de instrucciones (texto de prompts y tareas de los agentes), no de producto. No añade endpoints, no toca FastAPI, no toca el frontend, no persiste datos y no actualiza dependencias. Las decisiones cerradas del stack (FastAPI/Starlette, formato de error, identidad, persistencia, pins de versión) se evalúan en cada sección y se declara cuándo no aplican.

---

## 1. Resumen del cambio y alcance

### 1.1 Información explícita del Issue

- **Objetivo:** alinear las instrucciones de los agentes al contrato W2 y a la demo Angular web-only, "sin alterar los contratos ni el orden del pipeline".
- **Fuente de tareas:** `openspec/changes/proximity-contact-payment/tasks.md`, grupo 2 (tareas 2.1 a 2.6).
- **Referencias adicionales:** `openspec/changes/proximity-contact-payment/design.md`, sección "Instrucciones de agentes por alcance".
- **Contratos fuente:** `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt`.
- **Identificadores a preservar:** `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent`, `build_task(feature)`.
- **Extracción/publicación a preservar:** `frontend-angular/` → `web/`.
- **Validación:** pruebas de contratos existentes y `python tools/verify.py`. Si fallan, el fallo se documenta con la salida real.

### 1.2 Dentro del alcance

| # | Tarea | Resultado esperado en las instrucciones |
|---|---|---|
| 2.1 | Arquitectura | Usa `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt` como contratos fuente. Propone una página Angular, no un API propio. |
| 2.2 | Backend | Entrega `backend_spec.md` con la frase «Sin cambios en backend» y documenta solo el contrato externo W2. |
| 2.3 | Frontend | Exige Angular 17 standalone, servicios tipados, `environment.ts`, estados, accesibilidad e idempotencia. Preserva la extracción/publicación `frontend-angular/` → `web/`. |
| 2.4 | Pruebas | Cubre navegador/mock y propone solo comandos disponibles. No inventa `tools/lab.py` ni `ng test`. |
| 2.5 | Seguridad y Chapter | Revisa datos ficticios, errores, controles `/control/*`, CORS y criterios H03 adaptados. No exige autenticación, cambios FastAPI ni QR fuera de alcance. |
| 2.6 | Verificación | Ejecuta las pruebas de contratos y `python tools/verify.py`. Preserva los identificadores y el orden del pipeline. |

### 1.3 Fuera del alcance

- Cambios en el backend FastAPI (`api/app/`: `main.py`, `routers/`, `services.py`, `schemas.py`, `config.py`). El Issue pide explícitamente "Sin cambios en backend".
- Cambios en `bcp-wallet-mock-openapi.yaml` o `detalle H3.txt`, que son contratos fuente.
- Cambios en el código de la demo Angular. Solo se ajustan las instrucciones que guían a los agentes.
- Autenticación, identidad de usuario y QR (2.5 lo excluye).
- Actualización de dependencias: el Issue no la pide y no se tocan `requirements*.txt`.
- Creación de `tools/lab.py` o de un target `ng test` (2.4 lo prohíbe).
- Cambio de nombres, orden o semántica de los pasos del pipeline.

---

## 2. Componentes afectados, sus responsabilidades y límites

La ubicación física de los archivos de los agentes no figura en el Issue. Se identifican por rol e identificadores (`KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent`, `build_task(feature)`). La ruta exacta queda como pregunta pendiente en la sección 5.

| Componente | Responsabilidad en este cambio | Límite (qué no se toca) |
|---|---|---|
| Instrucciones del agente de **Arquitectura** | Fijar los contratos fuente (`bcp-wallet-mock-openapi.yaml`, `detalle H3.txt`) y proponer una página Angular sin API propia (2.1). | No introduce endpoints nuevos ni diseña un backend. |
| Instrucciones del agente de **Backend** | Exigir `backend_spec.md` con «Sin cambios en backend» y solo el contrato externo W2 (2.2). | No pide cambios en FastAPI ni documenta endpoints propios. |
| Instrucciones del agente de **Frontend** | Exigir Angular 17 standalone, servicios tipados, `environment.ts`, estados, accesibilidad e idempotencia (2.3). Preservar la extracción `frontend-angular/` → `web/`. | No altera `SPEC_FILE`, `EXTRACT_CODE` ni la ruta de publicación. |
| Instrucciones del agente de **Pruebas** | Cubrir navegador/mock y proponer solo comandos existentes (2.4). | No menciona `tools/lab.py` ni `ng test` como comandos a ejecutar. |
| Instrucciones del agente de **Seguridad y Chapter** | Revisar datos ficticios, errores, `/control/*`, CORS y criterios H03 adaptados (2.5). | No exige autenticación, cambios FastAPI ni QR. |
| Estructura de cada agente (`KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent`, `build_task(feature)`) y orden del pipeline | **Solo se preserva** (2.6). | Cualquier modificación incumple el criterio 3. |
| `tools/verify.py` y pruebas de contratos existentes | Sirven de verificación (2.6). | No se modifican para que pasen. Los fallos se documentan con salida real. |

**Límite general:** solo cambia el texto de las instrucciones. Los diffs no deben tocar código de producto, contratos fuente ni `requirements*.txt`.

---

## 3. Contrato de API relevante

### 3.1 Contrato propio de este cambio

**No hay contrato de API nuevo.** El Issue no agrega ni modifica endpoints, entradas, respuestas ni errores. Por eso no se definen códigos HTTP, cuerpos de error ni ejemplos de petición propios. Hacerlo contradiría "Sin cambios en backend" y "proponer página Angular, no API propia".

### 3.2 Contrato externo W2 (solo referencia)

- El contrato W2 vive en `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt`. Su contenido no está en el contexto recibido, así que **no se transcribe ni se infiere ninguna ruta, esquema ni código de error**.
- Lo único que el Issue nombra explícitamente es la familia de controles `/control/*`, que 2.5 pide revisar. No se asume que existan rutas concretas bajo ese prefijo.
- **Información que falta para documentar el contrato W2:** el contenido de ambos archivos (rutas, métodos, esquemas, códigos de error, mecanismo de idempotencia esperado, cabeceras CORS).
- **Regla de las instrucciones actualizadas:** el agente de Backend debe documentar el contrato W2 copiando lo que digan esos archivos y no inventando detalles.

### 3.3 Decisiones cerradas del stack y su aplicabilidad

| Decisión | Aplicación a este cambio |
|---|---|
| Formato de error único `{"code","message"}` con HTTP y `code` por error (p. ej. 413, 401). | **No aplica**, porque no se crea ni cambia ningún endpoint FastAPI. Supuesto A1: si el contrato W2 define su propio formato de error, prevalece el del contrato externo, y las instrucciones no deben imponer otro. |
| Ubicación física: `api/app/` (`main.py`, `routers/`, `services.py`, `schemas.py`, `config.py`) y pruebas en `api/tests/`. | **No hay archivos nuevos bajo `api/app/`.** Si las pruebas de contratos existentes están en `api/tests/`, solo se ejecutan, no se modifican (ver A4). |
| Identidad (dependencia de FastAPI, formato, directorio por SHA-256). | **No aplica.** 2.5 prohíbe exigir autenticación. Supuesto A2: no se introduce identidad de usuario. Ningún valor derivado de un propietario se expone, porque no hay propietarios. |
| Riesgos de persistencia (concurrencia, archivos preexistentes, migración). | **No aplica.** Ver A3: no se crea almacenamiento. El único riesgo cercano es de publicación (sobrescritura de `web/` por `frontend-angular/`), que se mitiga al no tocar `EXTRACT_CODE`. |
| Actualización de dependencias con `==` (incluido starlette). | **No aplica.** El Issue no pide actualizar paquetes. No se tocan `requirements*.txt`, no se consultaron datos de PyPI/OSV y no se proponen versiones. Si en el futuro se pidiera, cada paquete (incluido starlette) debe fijarse con `==` y confirmarse con PyPI y OSV. |

---

## 4. Trazabilidad de criterios de aceptación

### 4.1 Criterios de aceptación del Issue

| ID | Criterio | Componente responsable | Cómo comprobarlo |
|---|---|---|---|
| CA1 | Las instrucciones describen correctamente el alcance web-only y las responsabilidades/entregables indicados. | Instrucciones de Arquitectura, Backend, Frontend, Pruebas y Seguridad/Chapter. | Revisión del diff: `git diff` y `git diff --stat`. Cada tarea 2.1 a 2.5 debe tener un cambio localizable en el texto del agente correspondiente (checklist de 4.2). Comprobaciones textuales con `git grep -n "Sin cambios en backend"`, `git grep -n "Angular 17"`, `git grep -n "environment.ts"`, `git grep -n "bcp-wallet-mock-openapi.yaml"` y `git grep -n "detalle H3.txt"`. |
| CA2 | Las pruebas existentes y `python tools/verify.py` pasan, o sus fallos quedan documentados con salida real. | `tools/verify.py` y pruebas de contratos (solo se ejecutan). | Ejecutar `python tools/verify.py` y registrar código de salida (`echo $?`) y salida completa. Ejecutar las pruebas de contratos existentes (comando por confirmar, ver P3). Si fallan, pegar la salida real sin resumirla. |
| CA3 | No cambian identificadores, extracción, publicación ni orden del pipeline. | Estructura de los agentes (`KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent`, `build_task(feature)`) y definición del pipeline. | `git diff -U0` no debe mostrar líneas modificadas en las asignaciones de `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, en la firma de `build_task(feature)` ni en el orden de los agentes. Se comprueba con `git grep -nE "^(KEY\|LABEL\|SPEC_FILE\|EXTRACT_CODE)\b"` antes y después, comparando la salida. Si existen pruebas de contrato del pipeline, deben seguir pasando. |

### 4.2 Trazabilidad de las tareas 2.1 a 2.6

| Tarea | Criterio que la cubre | Componente | Verificación |
|---|---|---|---|
| 2.1 | CA1 | Instrucciones de Arquitectura | El texto cita ambos contratos fuente y pide "página Angular". No hay mención a un API propio como entregable. Se comprueba con `git grep` de los dos nombres de archivo y revisión del diff. |
| 2.2 | CA1 | Instrucciones de Backend | El texto exige `backend_spec.md` con «Sin cambios en backend» y limita el contenido al contrato externo W2. Se comprueba con `git grep -n "Sin cambios en backend"`. |
| 2.3 | CA1, CA3 | Instrucciones de Frontend | El texto exige Angular 17 standalone, servicios tipados, `environment.ts`, estados, accesibilidad e idempotencia. La extracción `frontend-angular/` → `web/` queda intacta (`git diff -U0` sin cambios en `EXTRACT_CODE`). |
| 2.4 | CA1 | Instrucciones de Pruebas | El texto cubre navegador/mock y solo cita comandos existentes. Se comprueba que el diff no añade `tools/lab.py` ni `ng test` como comandos a ejecutar. Las menciones prohibitivas ("no usar `ng test`") son aceptables. |
| 2.5 | CA1 | Instrucciones de Seguridad y Chapter | El texto lista datos ficticios, errores, `/control/*`, CORS y criterios H03 adaptados. No exige autenticación, cambios FastAPI ni QR. Se revisa el diff y se confirma con `git grep -niE "autenticaci\|QR"` sobre las líneas añadidas. |
| 2.6 | CA2, CA3 | `tools/verify.py`, pruebas de contratos, estructura de agentes | Evidencia de ejecución (comando, salida real y código de salida). Diff sin cambios en identificadores ni orden. |

### 4.3 Brecha de verificación declarada

No existe prueba automática conocida que valide el **contenido textual** de las instrucciones (CA1). Esa verificación es revisión manual del diff más `git grep`. Si `tools/verify.py` ya valida contenido o identificadores, esa cobertura es adicional. Su alcance real se desconoce (P4). Se pide a una persona aceptar esta brecha o indicar una prueba existente que la cubra.

---

## 5. Supuestos y preguntas pendientes

### 5.1 Supuestos (decisiones conservadoras)

| ID | Supuesto | Decisión conservadora |
|---|---|---|
| A1 | El formato de error del contrato W2 lo define `bcp-wallet-mock-openapi.yaml`. | Las instrucciones remiten a ese contrato. No se impone `{"code","message"}` a un API que este Issue no modifica. Ese formato queda como convención para cualquier cambio futuro en FastAPI. |
| A2 | La demo web-only no requiere identidad de usuario. | Se sigue 2.5: no se exige autenticación ni derivación de directorios por SHA-256. No se expone ningún valor derivado de propietario. |
| A3 | El cambio no crea persistencia. | No hay riesgo de concurrencia por usuario, archivos preexistentes ni migración. Si algún agente generara archivos, se mantiene la extracción actual hacia `web/` sin cambios. |
| A4 | Las "pruebas de contratos existentes" ya están en el repositorio y no hay que escribir pruebas nuevas. | Solo se ejecutan. Si residen en `api/tests/`, no se modifican. |
| A5 | El Issue no pide actualizar dependencias. | No se modifican `requirements*.txt` ni se citan versiones. |
| A6 | La lista de instrucciones a modificar equivale a los cinco roles de 2.1 a 2.5. | No se crean agentes nuevos ni se reordena el pipeline. |
| A7 | La frase «Sin cambios en backend» debe aparecer literalmente en `backend_spec.md`. | Se usa el texto tal cual figura en 2.2. |

### 5.2 Preguntas pendientes

- **P1.** ¿En qué rutas están los archivos que definen `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent` y `build_task(feature)`? El Issue no los ubica y no se asume ninguna ruta.
- **P2.** ¿Cuál es el contenido de `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt`? Sin él no se puede detallar el contrato W2 (endpoints, errores, idempotencia, CORS, rutas bajo `/control/*`).
- **P3.** ¿Cuál es el comando exacto de las "pruebas de contratos"? Se propone `python -m pytest` sobre el directorio de pruebas existente, pero es un supuesto a confirmar. No se inventa ningún otro comando.
- **P4.** ¿`python tools/verify.py` valida los identificadores, la extracción/publicación y el orden del pipeline, o solo parte de ellos? Esto determina cuánta parte de CA3 está cubierta automáticamente.
- **P5.** ¿Qué comandos están disponibles para cubrir navegador/mock en 2.4? El Issue prohíbe `tools/lab.py` y `ng test`, pero no lista los permitidos.
- **P6.** ¿Cuál es el contenido exacto de "criterios H03 adaptados" en 2.5? Se necesita para poder verificarlos en la revisión de Seguridad y Chapter.
- **P7.** ¿Alguien acepta la brecha del apartado 4.3 (sin prueba automática del contenido textual de las instrucciones), o hay un mecanismo previsto?