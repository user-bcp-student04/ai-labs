AMBITO
Workspace ai-labs abierto en su raíz. Lee código solo en api.
Todas las rutas parten de la raíz. Lee README.md, RETO.md y
docs generales. Este pedido es de solo lectura; no escribas archivos.
Git se ejecuta desde la raíz; las pruebas propuestas usan cd api.
No leas ni modifiques código de auth ni web. Usa IDs H-API-NN y componente api.

CONTEXTO
La API FastAPI autentica con Bearer token y persiste datos en SQLite. Lee
README.md, RETO.md y docs/ENDPOINTS.md si existe. Localiza las rutas
GET /api/tasks, POST /api/tasks y GET /api/summary desde el recurso
HTTP hasta la consulta SQLite. Considera owner en los filtros y los campos
title, description, status, priority y owner en el cuerpo de tareas.
No des por cierta la lista de RETO.md.

OBJETIVO
Determinar si entradas del cliente llegan concatenadas a consultas SQL de
SQLite o se pasan como parámetros.

RESTRICCIONES
No edites código ni ejecutes ataques contra servicios remotos. Usa solo
código y datos ficticios locales. No cambies contratos ni leas otros
componentes. Propón pruebas; no las ejecutes ni afirmes que pasaron.

CRITERIOS DE ACEPTACIÓN
Identifica el recorrido de cada entrada hasta la consulta con archivo y línea.
Distingue concatenación, parametrización y cualquier caso no comprobado.
Propón pruebas locales con token válido e inválido y entradas con comilla en
owner y en campos de tarea. Indica resultados esperados según el contrato
observado: comportamiento de autenticación y respuestas de cada endpoint; si
el contrato admite la comilla, debe tratarse como dato literal, no alterar la
consulta. No afirmes que las pruebas pasaron si solo las propusiste.

FORMATO DE RESPUESTA
Tabla: afirmación | evidencia archivo:línea | comprobado o hipótesis |
prueba propuesta. Termina con preguntas abiertas y comandos no ejecutados.