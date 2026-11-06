# backend_spec.md

## 1. Resumen de la solución

**Sin cambios en backend.**

El Issue [H03] es un cambio de instrucciones de agentes (texto de prompts y tareas), no de producto. Por eso no se entrega código Python, ni `api/requirements.txt`, ni configuración nueva, ni SQL. Se conservan sin tocar:

- `api/app/main.py`
- `api/app/routers/`
- `api/app/services.py`
- `api/app/schemas.py`
- `api/app/config.py`
- `api/requirements.txt` y `requirements-dev.txt`

La demo es Angular web-only, y la arquitectura propone una página Angular, no un API propio. Este documento solo referencia el contrato externo W2, sin ampliarlo ni reinterpretarlo.

## 2. Stack y estructura de archivos

- **Stack del API:** Python con FastAPI (Starlette), según el Issue y el plan de Arquitectura. No se usa Java, Quarkus ni Maven. En el material recibido no hay documentos previos que indiquen otro stack.
- **Archivos creados o modificados por el backend en este cambio:** ninguno.

```text
api/
  app/            (sin cambios)
    main.py
    routers/
    services.py
    schemas.py
    config.py
  requirements.txt   (sin cambios)
  tests/             (sin cambios)
```

Los archivos que definen `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent` y `build_task(feature)` están fuera del alcance de este rol. Su ruta no consta en el Issue (pendiente P1).

## 3. Tabla de endpoints

### 3.1 Endpoints propios

| Método | Ruta | Entrada | Respuesta | Errores |
|---|---|---|---|---|
| — | — | — | — | — |

**No hay endpoints propios.** El Issue no agrega ni modifica endpoints, y definirlos contradiría «Sin cambios en backend» y «página Angular, no API propia».

### 3.2 Contrato externo W2 (solo referencia)

- **Fuentes:** `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt`.
- **Contenido no disponible:** ninguno de los dos archivos figura en el contexto recibido. Por eso **no se transcribe ni se infiere** ninguna ruta, método, esquema, código de error, mecanismo de idempotencia ni cabecera CORS.
- **Único dato que el Issue nombra:** la familia de controles `/control/*`, que Seguridad y Chapter deben revisar (tarea 2.5). No se asume qué rutas concretas hay bajo ese prefijo.
- **Regla para completar esta sección:** cuando se aporte el contenido de los contratos, se copia fielmente de ellos. No se inventan detalles ni se cambia el contrato.

## 4. Reglas de validación

No aplican. No hay entradas nuevas en el servidor FastAPI. Cualquier validación de W2 es la que defina `bcp-wallet-mock-openapi.yaml`, y este cambio no la altera.

## 5. Manejo de errores

- No se registran ni se modifican handlers en FastAPI.
- El formato único `{"code": "...", "message": "..."}` sigue siendo la convención del stack para cambios futuros en FastAPI. **No se impone** al contrato W2 (supuesto A1): si `bcp-wallet-mock-openapi.yaml` define otro formato de error, prevalece el del contrato externo.

## 6. Límites y archivos

No aplica. No hay subidas de archivos, límites de tamaño ni middleware nuevo. Tampoco hay identidad ni aislamiento por propietario, ya que 2.5 prohíbe exigir autenticación (supuesto A2).

## 7. Origen de la persistencia

- **No hay base de datos ni almacenamiento nuevo.** Por eso no se emite SQL ni migración.
- No hay contrato de Datos en el contexto y el Issue no usa base de datos.
- No hay concurrencia por usuario ni archivos preexistentes que tratar (supuesto A3).
- Sobre la publicación `frontend-angular/` → `web/`: no se toca `EXTRACT_CODE`, así que no cambia.

## 8. Recorrido de un caso válido y de un caso de error

Como no hay endpoint propio, no hay recorrido «entrada → almacenamiento» en el backend. Los casos aplicables son del cambio de instrucciones:

- **Caso válido:** el diff del cambio no toca nada bajo `api/`, ni `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, la firma de `build_task(feature)` ni el orden del pipeline. `backend_spec.md` contiene «Sin cambios en backend» y se limita al contrato externo W2.
- **Caso de error:** el diff modifica archivos bajo `api/app/`, o añade endpoints o dependencias, o un agente de Backend documenta rutas propias. Esto viola el Issue y debe revertirse o escalarse.

## 9. Supuestos y pendientes

**Supuestos (decisión conservadora)**

- **S1.** El Issue manda sobre el prompt genérico del rol. El prompt pide código FastAPI, `api/requirements.txt` y SQL. El Issue (2.2) ordena «Sin cambios en backend», así que no se entregan esos archivos. Entregar código inventado rompería el alcance y el contrato.
- **S2.** El formato de error del contrato W2 lo define `bcp-wallet-mock-openapi.yaml` (A1).
- **S3.** No hay identidad ni autenticación (A2), ni persistencia (A3).
- **S4.** No se actualizan dependencias, así que no se tocan `requirements*.txt` ni se proponen versiones (A5).
- **S5.** Las pruebas de contratos ya existen. Solo se ejecutan y no se modifican (A4).
- **S6.** El comando de pruebas `python tools/lab.py test api` del prompt genérico **no se usa**, porque 2.4 prohíbe inventar `tools/lab.py` y `ng test`. Se propone `python -m pytest` (ver P3) y `python tools/verify.py`.
- **S7.** No se levanta `uvicorn`, porque no hay cambios en el servicio.

**Pendientes**

- **P1.** Ruta de los archivos que definen `KEY`, `LABEL`, `SPEC_FILE`, `EXTRACT_CODE`, `agent` y `build_task(feature)`.
- **P2.** Contenido de `bcp-wallet-mock-openapi.yaml` y `detalle H3.txt`. Es necesario para documentar el contrato W2 (rutas, errores, idempotencia, CORS, `/control/*`).
- **P3.** Comando exacto de las pruebas de contratos. `python -m pytest` es un supuesto sin confirmar.
- **P4.** Alcance real de `python tools/verify.py` sobre identificadores, extracción/publicación y orden del pipeline.
- **P5.** Comandos disponibles para cubrir navegador/mock (tarea 2.4).
- **P6.** Contenido de los «criterios H03 adaptados» (tarea 2.5).
- **P7.** Aceptar la brecha: no hay prueba automática del contenido textual de las instrucciones. Se verifica por revisión del diff y `git grep`.

## 10. Verificación

Todos los resultados están **NO EJECUTADO**. La persona que los ejecute debe conservar la salida real.

**Caso válido: no hay cambios en el backend**

```bash
git diff --stat -- api/
git diff --name-only -- api/app api/requirements.txt
```

- Resultado esperado: salida vacía en ambos comandos (sin diferencias bajo `api/`).
- Estado: **NO EJECUTADO**.

**Caso de error: detectar cambios no permitidos**

```bash
git diff --name-only -- api/app api/requirements.txt requirements-dev.txt | grep . && echo "VIOLACION: hay cambios en backend/dependencias"
```

- Resultado esperado si el cambio es correcto: sin salida y código de salida 1 de `grep`. Si imprime archivos y la frase «VIOLACION», el alcance fue incumplido.
- Estado: **NO EJECUTADO**.

**Comprobaciones textuales del entregable**

```bash
git grep -n "Sin cambios en backend"
git grep -n "bcp-wallet-mock-openapi.yaml"
git grep -n "detalle H3.txt"
```

- Resultado esperado: al menos una coincidencia por comando en las instrucciones actualizadas.
- Estado: **NO EJECUTADO**.

**Pruebas de contratos y verificación del repositorio**

```bash
python -m pytest
python tools/verify.py
echo $?
```

- `python -m pytest` es un supuesto pendiente de confirmar (P3).
- Resultado esperado: sin fallos y código de salida 0. Si hay fallos, se documentan con la salida real.
- Estado: **NO EJECUTADO**.

**No aplican en este cambio:**

- `uvicorn app.main:app --reload`: el servicio no cambia.
- `curl` contra endpoints propios: no existen.
- `pip install`, `pip check` y `pip freeze`: no se actualizan dependencias.
- `python tools/lab.py test api`: prohibido por 2.4.